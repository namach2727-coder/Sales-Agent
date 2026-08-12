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
        return list(self.session.scalars(select(SaasPlan).where(SaasPlan.is_active.is_(True)).order_by(SaasPlan.price_amount, SaasPlan.code)).all())

    def create_order(self, principal: AuthenticatedPrincipal, plan_public_id: str) -> SubscriptionOrder:
        tenant, store = self.customer_scope(principal)
        plan = self.session.scalar(select(SaasPlan).where(SaasPlan.public_id == plan_public_id, SaasPlan.is_active.is_(True)))
        if plan is None:
            raise CommerceNotFound("plan not found")
        order = SubscriptionOrder(
            tenant_id=tenant.id,
            store_id=store.id,
            user_id=principal.user_id,
            plan_id=plan.id,
            status="pending",
            price_amount=plan.price_amount,
            currency=plan.currency,
        )
        self.session.add(order)
        self.session.flush()
        self._audit(tenant.id, store.id, principal.user_id, "order.created", "order", order.public_id, {"plan_code": plan.code})
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
            status="active",
            limits_json=self._limits(plan),
            starts_at=(started_at := now_utc()),
            current_period_end=(
                started_at + timedelta(days=plan.duration_days)
                if plan.duration_days is not None
                else None
            ),
        )
        self.session.add(subscription)
        self._apply_plan_modules(order.store_id, plan, subscription)
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
        return self.session.scalar(select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id, TenantSubscription.store_id == store.id, TenantSubscription.status == "active").order_by(TenantSubscription.id.desc()))

    def _activate_free_subscription(self, order: SubscriptionOrder, plan: SaasPlan) -> None:
        started_at = now_utc()
        subscription = TenantSubscription(
            tenant_id=order.tenant_id,
            store_id=order.store_id,
            plan_id=plan.id,
            order_id=order.id,
            payment_id=None,
            status="active",
            limits_json=self._limits(plan),
            starts_at=started_at,
            current_period_end=(
                started_at + timedelta(days=plan.duration_days)
                if plan.duration_days is not None
                else None
            ),
        )
        self.session.add(subscription)
        self._apply_plan_modules(order.store_id, plan, subscription)

    @staticmethod
    def _limits(plan: SaasPlan) -> dict[str, int]:
        return {"reply_limit": plan.reply_limit, "automation_limit": plan.automation_limit, "instagram_account_limit": plan.instagram_account_limit}

    def _apply_plan_modules(self, store_id: int, plan: SaasPlan, subscription: TenantSubscription) -> None:
        for code in plan.module_codes or []:
            if self.session.get(ModuleDefinition, code) is None:
                raise CommerceConflict("plan references an unavailable module")
            item = self.session.scalar(select(StoreModule).where(StoreModule.store_id == store_id, StoreModule.module_code == code))
            if item is None:
                item = StoreModule(store_id=store_id, module_code=code, status="active", currency=plan.currency, source="subscription", limits_json=self._limits(plan))
                self.session.add(item)
            else:
                item.status = "active"
                item.source = "subscription"
                item.limits_json = self._limits(plan)

    def _audit(self, tenant_id: int, store_id: int | None, actor_user_id: int | None, action: str, target_type: str, target_public_id: str, details: dict[str, object]) -> None:
        self.session.add(CommerceAuditLog(tenant_id=tenant_id, store_id=store_id, actor_user_id=actor_user_id, action=action, target_type=target_type, target_public_id=target_public_id, details_json=details))
