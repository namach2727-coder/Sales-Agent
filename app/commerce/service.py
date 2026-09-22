"""Transactional registration, order, payment, and subscription use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.passwords import PasswordService
from app.authentication.service import normalize_email
from app.models import (
    AuthRole,
    AuthTenantRoleAssignment,
    CommerceAuditLog,
    CommerceAdminAuditLog,
    IdentityAuditLog,
    ManualPayment,
    ModuleDefinition,
    SaasPlan,
    Store,
    StoreModule,
    SubscriptionOrder,
    Tenant,
    TenantAuditLog,
    TenantMembership,
    TenantSubscription,
    UserIdentity,
)
from app.tenant_management.domain import normalize_name, normalize_slug, normalize_subdomain
from app.module_catalog import effective_product_subscriptions, effective_subscription


class CommerceError(Exception):
    code = "commerce_error"


class CommerceValidationError(CommerceError):
    code = "validation_error"


class CommerceConflict(CommerceError):
    code = "conflict"


class CommerceNotFound(CommerceError):
    code = "not_found"


class CommerceForbidden(CommerceError):
    code = "forbidden"


def now_utc() -> datetime:
    return datetime.now(UTC)


class RegistrationService:
    """Atomically creates identity, tenant, first store, and owner membership."""

    def __init__(self, session: Session, *, passwords: PasswordService) -> None:
        self.session = session
        self.passwords = passwords

    def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str,
        tenant_name: str,
        tenant_slug: str,
        store_name: str,
        store_slug: str,
    ) -> tuple[UserIdentity, Tenant, Store]:
        if self.session.in_transaction():
            raise CommerceConflict("registration requires a clean transaction")
        normalized_email = normalize_email(email)
        display_name = normalize_name(display_name)
        tenant_name = normalize_name(tenant_name)
        tenant_slug = normalize_slug(tenant_slug)
        store_name = normalize_name(store_name)
        store_slug = normalize_slug(store_slug)
        password_hash = self.passwords.hash(password)
        timestamp = now_utc()
        try:
            with self.session.begin():
                if self.session.scalar(select(UserIdentity.id).where(UserIdentity.normalized_email == normalized_email)) is not None:
                    raise CommerceConflict("account already exists")
                if self.session.scalar(select(Tenant.id).where(Tenant.slug == tenant_slug)) is not None:
                    raise CommerceConflict("tenant slug is unavailable")
                owner_role = self.session.get(AuthRole, "tenant_owner")
                if owner_role is None:
                    raise CommerceConflict("authorization seeds are missing")
                identity = UserIdentity(
                    email=email.strip(),
                    normalized_email=normalized_email,
                    display_name=display_name,
                    password_hash=password_hash,
                    status="active",
                    email_verified=False,
                    password_changed_at=timestamp,
                )
                self.session.add(identity)
                self.session.flush()
                tenant = Tenant(
                    name=tenant_name,
                    slug=tenant_slug,
                    status="active",
                    created_by_identity_id=identity.id,
                )
                self.session.add(tenant)
                self.session.flush()
                store = Store(
                    tenant_id=tenant.id,
                    name=store_name,
                    slug=store_slug,
                    status="onboarding",
                    subdomain=normalize_subdomain(tenant_slug),
                )
                self.session.add(store)
                self.session.flush()
                membership = TenantMembership(
                    user_id=identity.id,
                    tenant_id=tenant.id,
                    principal_type="user",
                    principal_id=str(identity.id),
                    status="active",
                    all_store_access=True,
                    activated_at=timestamp,
                )
                self.session.add(membership)
                self.session.flush()
                self.session.add(AuthTenantRoleAssignment(membership_id=membership.id, role_code="tenant_owner", status="active"))
                self.session.add(IdentityAuditLog(event_code="identity.registered", target_user_id=identity.id, tenant_id=tenant.id))
                self.session.add(TenantAuditLog(tenant_id=tenant.id, store_id=store.id, actor_identity_id=identity.id, action="tenant.self_registered", target_type="tenant", target_public_id=tenant.public_id, details_json={"initial_store_public_id": store.public_id}))
                # New customers receive the backend-authoritative Trial plan in
                # the same transaction as their identity, tenant, and store.
                # CommerceService owns order/subscription construction so this
                # registration path cannot drift from normal free-plan orders.
                CommerceService(self.session).activate_trial(
                    tenant=tenant,
                    store=store,
                    user_id=identity.id,
                )
            return identity, tenant, store
        except IntegrityError as exc:
            self.session.rollback()
            raise CommerceConflict("registration conflicts with existing data") from exc


class CommerceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def customer_scope(self, principal: AuthenticatedPrincipal) -> tuple[Tenant, Store]:
        active = [item for item in principal.tenant_memberships if item.status == "active"]
        if not active:
            raise CommerceForbidden("active tenant membership required")
        membership = active[0]
        tenant = self.session.get(Tenant, membership.tenant_id)
        if tenant is None or tenant.status != "active" or tenant.deleted_at is not None:
            raise CommerceForbidden("active tenant required")
        store = self.session.scalar(
            select(Store).where(
                Store.tenant_id == tenant.id,
                Store.deleted_at.is_(None),
                Store.status.in_(("onboarding", "active")),
            ).order_by(Store.id)
        )
        if store is None:
            raise CommerceForbidden("active store required")
        return tenant, store

    def list_plans(self) -> list[SaasPlan]:
        return list(self.session.scalars(select(SaasPlan).where(
            SaasPlan.is_active.is_(True), SaasPlan.is_purchasable.is_(True)
        ).order_by(SaasPlan.display_order, SaasPlan.price_amount, SaasPlan.code)).all())

    @staticmethod
    def _validate_plan_policy(*, product_family: str, module_codes: list[str]) -> None:
        expected = {
            "AUTOMATION": {"instagram_automation"},
            "AI_ASSISTANT": {"ai_assistant", "knowledge_base"},
        }
        if product_family not in expected or set(module_codes) != expected[product_family]:
            raise CommerceValidationError("invalid product capability mapping")

    @staticmethod
    def _validate_sellable_policy(*, price_amount: int, is_purchasable: bool, trial_eligible: bool) -> None:
        if is_purchasable and price_amount <= 0 and not trial_eligible:
            raise CommerceValidationError("a purchasable paid plan requires a positive price")

    def admin_plans(self) -> list[SaasPlan]:
        return list(self.session.scalars(select(SaasPlan).order_by(SaasPlan.display_order, SaasPlan.code)).all())

    def admin_create_plan(self, *, actor_user_id: int, **values: object) -> SaasPlan:
        family = str(values["product_family"])
        modules = ["instagram_automation"] if family == "AUTOMATION" else ["ai_assistant", "knowledge_base"]
        self._validate_plan_policy(product_family=family, module_codes=modules)
        self._validate_sellable_policy(
            price_amount=int(values["price_amount"]),
            is_purchasable=bool(values["is_purchasable"]),
            trial_eligible=bool(values["trial_eligible"]),
        )
        if self.session.scalar(select(SaasPlan.id).where(SaasPlan.code == values["code"])) is not None:
            raise CommerceConflict("plan code already exists")
        plan = SaasPlan(module_codes=modules, revision=1, **values)
        self.session.add(plan)
        self.session.flush()
        self._admin_audit(actor_user_id, "commercial_plan.created", "saas_plan", plan.public_id, {"fields": sorted(values)})
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def admin_update_plan(self, public_id: str, *, actor_user_id: int, expected_revision: int, **changes: object) -> SaasPlan:
        plan = self.session.scalar(select(SaasPlan).where(SaasPlan.public_id == public_id))
        if plan is None:
            raise CommerceNotFound("plan not found")
        if plan.revision != expected_revision:
            raise CommerceConflict("revision conflict")
        if plan.product_family == "LEGACY_BUNDLE":
            raise CommerceForbidden("legacy plans are immutable")
        applied = {key: value for key, value in changes.items() if value is not None}
        if not applied:
            raise CommerceValidationError("at least one change is required")
        before = {key: getattr(plan, key) for key in applied}
        self._validate_sellable_policy(
            price_amount=int(applied.get("price_amount", plan.price_amount)),
            is_purchasable=bool(applied.get("is_purchasable", plan.is_purchasable)),
            trial_eligible=bool(applied.get("trial_eligible", plan.trial_eligible)),
        )
        for key, value in applied.items():
            setattr(plan, key, value)
        plan.revision += 1
        self._admin_audit(actor_user_id, "commercial_plan.updated", "saas_plan", plan.public_id, {"changed_fields": sorted(applied), "before": before, "after": applied})
        self.session.commit()
        self.session.refresh(plan)
        return plan

    def admin_subscriptions(self) -> list[TenantSubscription]:
        return list(self.session.scalars(select(TenantSubscription).order_by(TenantSubscription.id.desc())).all())

    def admin_grant(self, *, actor_user_id: int, tenant_public_id: str, store_public_id: str, plan_public_id: str, expires_at: datetime | None) -> TenantSubscription:
        tenant = self.session.scalar(select(Tenant).where(Tenant.public_id == tenant_public_id))
        store = self.session.scalar(select(Store).where(Store.public_id == store_public_id))
        plan = self.session.scalar(select(SaasPlan).where(SaasPlan.public_id == plan_public_id, SaasPlan.is_active.is_(True)))
        if tenant is None or store is None or store.tenant_id != tenant.id or plan is None:
            raise CommerceNotFound("commercial scope not found")
        if plan.product_family == "LEGACY_BUNDLE":
            raise CommerceForbidden("legacy bundle cannot be granted")
        started = now_utc()
        subscription = TenantSubscription(
            tenant_id=tenant.id, store_id=store.id, plan_id=plan.id,
            order_id=None, payment_id=None, product_family=plan.product_family,
            source="ADMIN_GRANT", status="active", limits_json=self._limits(plan),
            starts_at=started, current_period_end=expires_at,
        )
        self.session.add(subscription)
        self.session.flush()
        self._apply_plan_modules(store.id, plan, subscription)
        self._audit(tenant.id, store.id, actor_user_id, "subscription.admin_granted", "tenant_subscription", subscription.public_id, {"product_family": plan.product_family, "plan_public_id": plan.public_id})
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def admin_revoke(self, public_id: str, *, actor_user_id: int) -> TenantSubscription:
        item = self.session.scalar(select(TenantSubscription).where(TenantSubscription.public_id == public_id))
        if item is None:
            raise CommerceNotFound("subscription not found")
        if item.source != "ADMIN_GRANT" or item.status != "active":
            raise CommerceConflict("only an active admin grant can be revoked")
        item.status = "cancelled"
        self._audit(item.tenant_id, item.store_id, actor_user_id, "subscription.admin_revoked", "tenant_subscription", item.public_id, {"product_family": item.product_family})
        self.session.commit()
        self.session.refresh(item)
        return item

    def create_order(self, principal: AuthenticatedPrincipal, plan_public_id: str) -> SubscriptionOrder:
        tenant, store = self.customer_scope(principal)
        plan = self.session.scalar(select(SaasPlan).where(
            SaasPlan.public_id == plan_public_id,
            SaasPlan.is_active.is_(True),
            SaasPlan.is_purchasable.is_(True),
        ))
        if plan is None:
            raise CommerceNotFound("plan not found")
        if plan.code == "TRIAL":
            existing_subscription = self.session.scalar(
                select(TenantSubscription)
                .where(
                    TenantSubscription.tenant_id == tenant.id,
                    TenantSubscription.store_id == store.id,
                    TenantSubscription.plan_id == plan.id,
                    TenantSubscription.status == "active",
                )
                .order_by(TenantSubscription.id.desc())
            )
            if existing_subscription is not None:
                existing_order = self.session.get(
                    SubscriptionOrder, existing_subscription.order_id
                )
                if existing_order is not None:
                    return existing_order
        order = self._create_order(
            tenant=tenant,
            store=store,
            user_id=principal.user_id,
            plan=plan,
        )
        if plan.price_amount == 0:
            order.status = "paid"
            self._activate_free_subscription(order, plan)
        self.session.commit()
        self.session.refresh(order)
        return order

    def list_orders(self, principal: AuthenticatedPrincipal) -> list[SubscriptionOrder]:
        tenant, _ = self.customer_scope(principal)
        return list(self.session.scalars(select(SubscriptionOrder).where(SubscriptionOrder.tenant_id == tenant.id, SubscriptionOrder.user_id == principal.user_id).order_by(SubscriptionOrder.id.desc())).all())

    def get_order(self, principal: AuthenticatedPrincipal, public_id: str) -> SubscriptionOrder:
        tenant, _ = self.customer_scope(principal)
        item = self.session.scalar(select(SubscriptionOrder).where(SubscriptionOrder.public_id == public_id, SubscriptionOrder.tenant_id == tenant.id, SubscriptionOrder.user_id == principal.user_id))
        if item is None:
            raise CommerceNotFound("order not found")
        return item

    def create_payment(self, principal: AuthenticatedPrincipal, order_public_id: str) -> ManualPayment:
        order = self.get_order(principal, order_public_id)
        if order.price_amount == 0 or order.status == "paid":
            raise CommerceConflict("order does not require payment")
        existing = self.session.scalar(select(ManualPayment).where(ManualPayment.order_id == order.id))
        if existing is not None:
            return existing
        payment = ManualPayment(
            tenant_id=order.tenant_id,
            store_id=order.store_id,
            order_id=order.id,
            user_id=principal.user_id,
            amount=order.price_amount,
            currency=order.currency,
            status="pending",
        )
        self.session.add(payment)
        self.session.flush()
        self._audit(order.tenant_id, order.store_id, principal.user_id, "payment.created", "payment", payment.public_id, {"provider": "manual_card_transfer"})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def list_payments(self, principal: AuthenticatedPrincipal) -> list[ManualPayment]:
        tenant, _ = self.customer_scope(principal)
        return list(self.session.scalars(select(ManualPayment).where(ManualPayment.tenant_id == tenant.id, ManualPayment.user_id == principal.user_id).order_by(ManualPayment.id.desc())).all())

    def get_owned_payment(self, principal: AuthenticatedPrincipal, public_id: str) -> ManualPayment:
        tenant, _ = self.customer_scope(principal)
        item = self.session.scalar(select(ManualPayment).where(ManualPayment.public_id == public_id, ManualPayment.tenant_id == tenant.id, ManualPayment.user_id == principal.user_id))
        if item is None:
            raise CommerceNotFound("payment not found")
        return item

    def submit_receipt(self, principal: AuthenticatedPrincipal, payment_public_id: str, *, storage_key: str, content_type: str, size: int, sha256: str) -> ManualPayment:
        payment = self.get_owned_payment(principal, payment_public_id)
        if payment.status not in {"pending", "rejected"}:
            raise CommerceConflict("payment cannot accept a receipt")
        payment.receipt_storage_key = storage_key
        payment.receipt_content_type = content_type
        payment.receipt_size = size
        payment.receipt_sha256 = sha256
        payment.status = "submitted"
        payment.submitted_at = now_utc()
        payment.rejected_at = None
        payment.rejection_reason = None
        payment.revision += 1
        order = self.session.get(SubscriptionOrder, payment.order_id)
        if order is not None:
            order.status = "payment_submitted"
        self._audit(payment.tenant_id, payment.store_id, principal.user_id, "payment.receipt_submitted", "payment", payment.public_id, {"content_type": content_type, "size": size})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def admin_payments(self) -> list[ManualPayment]:
        return list(self.session.scalars(select(ManualPayment).order_by(ManualPayment.id.desc())).all())

    def admin_payment(self, public_id: str) -> ManualPayment:
        payment = self.session.scalar(select(ManualPayment).where(ManualPayment.public_id == public_id))
        if payment is None:
            raise CommerceNotFound("payment not found")
        return payment

    def approve(self, payment_public_id: str, *, expected_revision: int, actor_user_id: int) -> ManualPayment:
        payment = self.session.scalar(
            select(ManualPayment)
            .where(ManualPayment.public_id == payment_public_id)
            .with_for_update()
        )
        if payment is None:
            raise CommerceNotFound("payment not found")
        if payment.status == "approved":
            return payment
        if payment.revision != expected_revision:
            raise CommerceConflict("revision conflict")
        if payment.status != "submitted" or not payment.receipt_storage_key:
            raise CommerceConflict("submitted receipt required")
        order = self.session.get(SubscriptionOrder, payment.order_id)
        plan = self.session.get(SaasPlan, order.plan_id if order else None)
        if order is None or plan is None or order.tenant_id != payment.tenant_id:
            raise CommerceConflict("payment order is invalid")
        payment.status = "approved"
        payment.approved_at = now_utc()
        payment.approved_by_user_id = actor_user_id
        payment.revision += 1
        order.status = "paid"
        subscription = TenantSubscription(
            tenant_id=order.tenant_id,
            store_id=order.store_id,
            plan_id=plan.id,
            order_id=order.id,
            payment_id=payment.id,
            product_family=self._order_product_family(order, plan),
            source="PURCHASED",
            status="active",
            limits_json=self._order_limits(order, plan),
            starts_at=(started_at := now_utc()),
            current_period_end=(
                started_at + timedelta(days=self._order_duration_days(order, plan))
                if self._order_duration_days(order, plan) is not None
                else None
            ),
        )
        self.session.add(subscription)
        self._apply_order_modules(order.store_id, order, plan, subscription)
        self._audit(payment.tenant_id, payment.store_id, actor_user_id, "payment.approved", "payment", payment.public_id, {"order_public_id": order.public_id})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def reject(self, payment_public_id: str, *, expected_revision: int, actor_user_id: int, reason: str | None) -> ManualPayment:
        payment = self.session.scalar(select(ManualPayment).where(ManualPayment.public_id == payment_public_id))
        if payment is None:
            raise CommerceNotFound("payment not found")
        if payment.revision != expected_revision:
            raise CommerceConflict("revision conflict")
        if payment.status != "submitted":
            raise CommerceConflict("only submitted payments can be rejected")
        payment.status = "rejected"
        payment.rejected_at = now_utc()
        payment.rejection_reason = (reason or "").strip() or None
        payment.revision += 1
        order = self.session.get(SubscriptionOrder, payment.order_id)
        if order is not None:
            order.status = "pending"
        self._audit(payment.tenant_id, payment.store_id, actor_user_id, "payment.rejected", "payment", payment.public_id, {"reason_recorded": bool(payment.rejection_reason)})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def subscription(self, principal: AuthenticatedPrincipal) -> TenantSubscription | None:
        tenant, store = self.customer_scope(principal)
        return effective_subscription(
            self.session,
            tenant_id=tenant.id,
            store_id=store.id,
        )

    def reconcile_subscription_modules(
        self, principal: AuthenticatedPrincipal
    ) -> TenantSubscription:
        """Reconcile the caller's effective subscription with its current plan.

        This operation repairs lifecycle entitlements only.  It deliberately
        leaves the subscription, order, dates, status, and limit snapshot
        unchanged.
        """
        tenant, store = self.customer_scope(principal)
        subscriptions = effective_product_subscriptions(
            self.session, tenant_id=tenant.id, store_id=store.id
        )
        if not subscriptions:
            raise CommerceConflict("active subscription required")
        for subscription in subscriptions:
            plan = self.session.get(SaasPlan, subscription.plan_id)
            if plan is None:
                raise CommerceConflict("subscription plan is unavailable")
            self._apply_plan_modules(store.id, plan, subscription)
        self.session.commit()
        subscription = effective_subscription(self.session, tenant_id=tenant.id, store_id=store.id)
        assert subscription is not None
        self.session.refresh(subscription)
        return subscription

    def activate_trial(self, *, tenant: Tenant, store: Store, user_id: int) -> TenantSubscription:
        """Atomically activate independent Automation and AI trials.

        The method participates in the caller's transaction and deliberately
        does not commit.  It reuses the same order and free-subscription
        primitives as the public order flow, while allowing registration to
        remain atomic before an authenticated principal exists.
        """
        plans = list(self.session.scalars(select(SaasPlan).where(
            SaasPlan.code.in_(("AUTOMATION_TRIAL", "AI_ASSISTANT_TRIAL")),
            SaasPlan.is_active.is_(True),
            SaasPlan.trial_eligible.is_(True),
        )).all())
        if {plan.product_family for plan in plans} != {"AUTOMATION", "AI_ASSISTANT"}:
            raise CommerceConflict("independent trial plans are unavailable")
        started_at = now_utc()
        subscriptions: list[TenantSubscription] = []
        for plan in sorted(plans, key=lambda item: item.product_family):
            existing = self.session.scalar(select(TenantSubscription).where(
                TenantSubscription.tenant_id == tenant.id,
                TenantSubscription.store_id == store.id,
                TenantSubscription.product_family == plan.product_family,
                TenantSubscription.source == "TRIAL",
                TenantSubscription.status == "active",
            ).order_by(TenantSubscription.id.desc()))
            if existing is not None:
                subscriptions.append(existing)
                continue
            order = self._create_order(tenant=tenant, store=store, user_id=user_id, plan=plan)
            order.status = "paid"
            subscriptions.append(self._activate_free_subscription(order, plan, started_at=started_at))
        self.session.flush()
        return subscriptions[0]

    def _create_order(
        self,
        *,
        tenant: Tenant,
        store: Store,
        user_id: int,
        plan: SaasPlan,
    ) -> SubscriptionOrder:
        order = SubscriptionOrder(
            tenant_id=tenant.id,
            store_id=store.id,
            user_id=user_id,
            plan_id=plan.id,
            status="pending",
            price_amount=plan.price_amount,
            currency=plan.currency,
            plan_code_snapshot=plan.code,
            plan_name_snapshot=plan.name,
            product_family_snapshot=plan.product_family,
            duration_days_snapshot=plan.duration_days,
            instagram_account_limit_snapshot=plan.instagram_account_limit,
            automation_limit_snapshot=plan.automation_limit,
            ai_reply_limit_snapshot=plan.reply_limit,
            ai_request_limit_snapshot=plan.ai_request_limit,
            ai_token_limit_snapshot=plan.ai_token_limit,
        )
        self.session.add(order)
        self.session.flush()
        self._audit(
            tenant.id,
            store.id,
            user_id,
            "order.created",
            "order",
            order.public_id,
            {"plan_code": plan.code},
        )
        return order

    def _activate_free_subscription(self, order: SubscriptionOrder, plan: SaasPlan, *, started_at: datetime | None = None) -> TenantSubscription:
        started_at = started_at or now_utc()
        subscription = TenantSubscription(
            tenant_id=order.tenant_id,
            store_id=order.store_id,
            plan_id=plan.id,
            order_id=order.id,
            payment_id=None,
            product_family=self._order_product_family(order, plan),
            source="TRIAL" if plan.trial_eligible else "PURCHASED",
            status="active",
            limits_json=self._order_limits(order, plan),
            starts_at=started_at,
            current_period_end=(
                started_at + timedelta(days=self._order_duration_days(order, plan))
                if self._order_duration_days(order, plan) is not None
                else None
            ),
        )
        self.session.add(subscription)
        self._apply_order_modules(order.store_id, order, plan, subscription)
        return subscription

    @staticmethod
    def _order_product_family(order: SubscriptionOrder, plan: SaasPlan) -> str:
        return order.product_family_snapshot or plan.product_family

    @staticmethod
    def _order_duration_days(order: SubscriptionOrder, plan: SaasPlan) -> int | None:
        return order.duration_days_snapshot if order.plan_code_snapshot is not None else plan.duration_days

    @staticmethod
    def _order_limits(order: SubscriptionOrder, plan: SaasPlan) -> dict[str, int]:
        if order.plan_code_snapshot is None:
            return CommerceService._limits(plan)
        limits = {
            "reply_limit": order.ai_reply_limit_snapshot or 0,
            "automation_limit": order.automation_limit_snapshot or 0,
            "instagram_account_limit": order.instagram_account_limit_snapshot or 0,
        }
        if order.ai_request_limit_snapshot is not None:
            limits["ai_request_limit"] = order.ai_request_limit_snapshot
        if order.ai_token_limit_snapshot is not None:
            limits["ai_token_limit"] = order.ai_token_limit_snapshot
        if order.duration_days_snapshot is not None:
            limits["duration_days"] = order.duration_days_snapshot
        return limits

    def _apply_order_modules(self, store_id: int, order: SubscriptionOrder, plan: SaasPlan, subscription: TenantSubscription) -> None:
        if order.plan_code_snapshot is None:
            self._apply_plan_modules(store_id, plan, subscription)
            return
        family = self._order_product_family(order, plan)
        desired_codes = {
            "AUTOMATION": {"instagram_automation"},
            "AI_ASSISTANT": {"ai_assistant", "knowledge_base"},
            "LEGACY_BUNDLE": {"instagram_automation", "ai_assistant", "knowledge_base"},
        }[family]
        self._apply_modules(store_id, desired_codes, family, order.currency, self._order_limits(order, plan))

    @staticmethod
    def _limits(plan: SaasPlan) -> dict[str, int]:
        limits = {"reply_limit": plan.reply_limit, "automation_limit": plan.automation_limit, "instagram_account_limit": plan.instagram_account_limit}
        if plan.ai_request_limit is not None:
            limits["ai_request_limit"] = plan.ai_request_limit
        if plan.ai_token_limit is not None:
            limits["ai_token_limit"] = plan.ai_token_limit
        if plan.duration_days is not None:
            limits["duration_days"] = plan.duration_days
        return limits

    def _apply_plan_modules(self, store_id: int, plan: SaasPlan, subscription: TenantSubscription) -> None:
        desired_codes = set(plan.module_codes or [])
        self._apply_modules(store_id, desired_codes, plan.product_family, plan.currency, self._limits(plan))

    def _apply_modules(self, store_id: int, desired_codes: set[str], product_family: str, currency: str, limits: dict[str, int]) -> None:
        family_codes = {
            "AUTOMATION": {"instagram_automation"},
            "AI_ASSISTANT": {"ai_assistant", "knowledge_base"},
            "LEGACY_BUNDLE": {"instagram_automation", "ai_assistant", "knowledge_base"},
        }[product_family]
        definitions = {
            item.code: item
            for item in self.session.scalars(
                select(ModuleDefinition).where(ModuleDefinition.code.in_(desired_codes))
            ).all()
        } if desired_codes else {}
        if definitions.keys() != desired_codes:
            raise CommerceConflict("plan references an unavailable module")

        existing_modules = {
            item.module_code: item
            for item in self.session.scalars(
                select(StoreModule).where(StoreModule.store_id == store_id)
            ).all()
        }
        for code, item in existing_modules.items():
            if item.source == "subscription" and code in family_codes and code not in desired_codes:
                item.status = "inactive"

        for code in sorted(desired_codes):
            item = existing_modules.get(code)
            if item is None:
                item = StoreModule(store_id=store_id, module_code=code, status="active", currency=currency, source="subscription", limits_json=limits)
                self.session.add(item)
            else:
                item.status = "active"
                item.source = "subscription"
                item.limits_json = limits

    def _reconcile_subscription_modules(
        self,
        *,
        tenant: Tenant,
        store: Store,
        subscription: TenantSubscription,
    ) -> None:
        if store.tenant_id != tenant.id or (
            subscription.tenant_id != tenant.id
            or subscription.store_id != store.id
            or subscription.status != "active"
        ):
            raise CommerceForbidden("subscription is outside the requested scope")
        effective = effective_subscription(
            self.session,
            tenant_id=tenant.id,
            store_id=store.id,
        )
        if effective is None or effective.id != subscription.id:
            raise CommerceConflict("subscription is not currently effective")
        plan = self.session.get(SaasPlan, subscription.plan_id)
        if plan is None:
            raise CommerceConflict("subscription plan is unavailable")
        self._apply_plan_modules(store.id, plan, subscription)

    def _audit(self, tenant_id: int | None, store_id: int | None, actor_user_id: int | None, action: str, target_type: str, target_public_id: str, details: dict[str, object]) -> None:
        self.session.add(CommerceAuditLog(tenant_id=tenant_id, store_id=store_id, actor_user_id=actor_user_id, action=action, target_type=target_type, target_public_id=target_public_id, details_json=details))

    def _admin_audit(self, actor_user_id: int, action: str, target_type: str, target_public_id: str, changes: dict[str, object]) -> None:
        self.session.add(CommerceAdminAuditLog(actor_user_id=actor_user_id, action=action, target_type=target_type, target_public_id=target_public_id, changes_json=changes))
