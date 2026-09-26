"""Customer and provider HTTP adapters for the sellable SaaS MVP."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import build_authentication_service, require_authenticated_principal, require_platform_permission
from app.authentication.exceptions import AuthenticationError, AuthenticationValidationError
from app.authentication.passwords import PasswordService
from app.authentication.schemas import LoginInput
from app.authz.permissions import PermissionCode
from app.commerce.schemas import (
    AdminPaymentRead,
    AdminGrantCreate,
    AdminCommerceAuditRead,
    AdminCustomerStoreRead,
    AdminPlanRead,
    AdminPlanUpdate,
    AdminPlanWrite,
    AdminRevokeInput,
    AdminSubscriptionRead,
    CardTransferCreate,
    CardTransferInstructions,
    KPayCreate,
    KPayPaymentRead,
    OrderCreate,
    OrderRead,
    PaymentDecision,
    PaymentRead,
    PlanRead,
    ProductSubscriptionRead,
    PublicLoginResponse,
    PublicMembership,
    PublicPrincipal,
    RegisterInput,
    RegisterResponse,
    SubscriptionRead,
)
from app.commerce.payment_provider import (
    ManualCardTransferProvider,
    PaymentProviderUnavailable,
)
from app.commerce.kpay_provider import (
    KPayClient,
    KPayConfigurationError,
    KPayProviderError,
)
from app.commerce.service import CommerceConflict, CommerceError, CommerceForbidden, CommerceNotFound, CommerceService, RegistrationService
from app.commerce.storage import LocalPrivateReceiptStorage, ReceiptValidationError
from app.config import Settings, get_settings
from app.database import get_db
from app.models import CommerceAdminAuditLog, CommerceAuditLog, ManualPayment, SaasPlan, Store, SubscriptionOrder, Tenant, TenantSubscription, UserIdentity
from app.module_catalog import effective_capabilities, effective_capabilities_for_stores, effective_product_subscriptions
from app.tenant_management.domain import TenantManagementError


router = APIRouter(prefix="/api/v1", tags=["saas-commerce"])


def _error(exc: CommerceError) -> None:
    status_code = 404 if isinstance(exc, CommerceNotFound) else 403 if isinstance(exc, CommerceForbidden) else 409 if isinstance(exc, CommerceConflict) else 422
    raise HTTPException(status_code=status_code, detail={"code": exc.code, "message": str(exc)})


def _public_principal(db: Session, principal: AuthenticatedPrincipal) -> PublicPrincipal:
    tenant_ids = [item.tenant_id for item in principal.tenant_memberships if item.status == "active"]
    tenants = {item.id: item for item in db.scalars(select(Tenant).where(Tenant.id.in_(tenant_ids))).all()} if tenant_ids else {}
    memberships = [
        PublicMembership(tenant_public_id=tenants[item.tenant_id].public_id, tenant_slug=item.tenant_slug, status=item.status)
        for item in principal.tenant_memberships
        if item.status == "active" and item.tenant_id in tenants
    ]
    return PublicPrincipal(email=principal.email, display_name=principal.display_name, session_public_id=principal.session_id, authenticated_at=principal.authenticated_at, tenant_memberships=memberships, platform_role_codes=list(principal.platform_role_codes))


@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> RegisterResponse:
    try:
        identity, tenant, store = RegistrationService(
            db,
            passwords=PasswordService(minimum_length=settings.password_min_length, maximum_length=settings.password_max_length),
        ).register(**payload.model_dump())
        return RegisterResponse(email=identity.email, display_name=identity.display_name, tenant_public_id=tenant.public_id, tenant_slug=tenant.slug, store_public_id=store.public_id, store_slug=store.slug)
    except CommerceError as exc:
        _error(exc)
    except (ValueError, AuthenticationValidationError, TenantManagementError) as exc:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": str(exc)}) from exc


@router.post("/auth/login", response_model=PublicLoginResponse)
def api_login(payload: LoginInput, request: Request, response: Response, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> PublicLoginResponse:
    email, password = payload.email, payload.password
    try:
        credential = build_authentication_service(db, settings).authenticate_password(email=email, password=password, user_agent=request.headers.get("user-agent"))
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": "Invalid credentials"}) from exc
    response.set_cookie(settings.session_cookie_name, credential.token, max_age=settings.session_ttl_minutes * 60, httponly=True, secure=settings.session_cookie_secure, samesite=settings.session_cookie_samesite, path="/")
    return PublicLoginResponse(access_token=credential.token, expires_at=credential.expires_at, principal=_public_principal(db, credential.principal))


@router.post("/auth/logout")
def api_logout(response: Response, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, str]:
    build_authentication_service(db, settings).revoke_session(session_id=principal.session_id, actor_user_id=principal.user_id)
    response.delete_cookie(settings.session_cookie_name, path="/", secure=settings.session_cookie_secure, httponly=True, samesite=settings.session_cookie_samesite)
    return {"status": "revoked"}


@router.get("/auth/me", response_model=PublicPrincipal)
def api_me(principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> PublicPrincipal:
    return _public_principal(db, principal)


@router.get("/plans", response_model=list[PlanRead])
def plans(db: Session = Depends(get_db)) -> list[PlanRead]:
    return [PlanRead.model_validate(item, from_attributes=True) for item in CommerceService(db).list_plans()]


def _order_read(db: Session, item: SubscriptionOrder) -> OrderRead:
    tenant, store, plan = db.get(Tenant, item.tenant_id), db.get(Store, item.store_id), db.get(SaasPlan, item.plan_id)
    assert tenant is not None and store is not None and plan is not None
    return OrderRead(
        public_id=item.public_id, tenant_public_id=tenant.public_id,
        store_public_id=store.public_id, plan_public_id=plan.public_id,
        plan_code=item.plan_code_snapshot or plan.code,
        plan_name=item.plan_name_snapshot or plan.name,
        product_family=item.product_family_snapshot or plan.product_family,
        duration_days=item.duration_days_snapshot if item.duration_days_snapshot is not None else plan.duration_days,
        instagram_account_limit=item.instagram_account_limit_snapshot if item.instagram_account_limit_snapshot is not None else plan.instagram_account_limit,
        automation_limit=item.automation_limit_snapshot if item.automation_limit_snapshot is not None else plan.automation_limit,
        ai_reply_limit=item.ai_reply_limit_snapshot if item.ai_reply_limit_snapshot is not None else plan.reply_limit,
        ai_request_limit=item.ai_request_limit_snapshot if item.plan_code_snapshot is not None else plan.ai_request_limit,
        ai_token_limit=item.ai_token_limit_snapshot if item.plan_code_snapshot is not None else plan.ai_token_limit,
        status=item.status, price_amount=item.price_amount, currency=item.currency,
        created_at=item.created_at,
    )


@router.post("/orders", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> OrderRead:
    try:
        return _order_read(db, CommerceService(db).create_order(principal, payload.plan_public_id))
    except CommerceError as exc:
        _error(exc)


@router.get("/orders/me", response_model=list[OrderRead])
def my_orders(principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> list[OrderRead]:
    try:
        return [_order_read(db, item) for item in CommerceService(db).list_orders(principal)]
    except CommerceError as exc:
        _error(exc)


@router.get("/orders/{order_public_id}", response_model=OrderRead)
def order(order_public_id: str, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> OrderRead:
    try:
        return _order_read(db, CommerceService(db).get_order(principal, order_public_id))
    except CommerceError as exc:
        _error(exc)


def _payment_read(db: Session, item: ManualPayment) -> PaymentRead:
    order = db.get(SubscriptionOrder, item.order_id)
    assert order is not None
    return PaymentRead(public_id=item.public_id, order_public_id=order.public_id, status=item.status, amount=item.amount, currency=item.currency, revision=item.revision, receipt_configured=bool(item.receipt_storage_key), created_at=item.created_at)


def _kpay_read(db: Session, item: ManualPayment) -> KPayPaymentRead:
    return KPayPaymentRead(
        payment=_payment_read(db, item),
        operation_state=item.provider_operation_state or "NOT_STARTED",
        payment_url=item.provider_payment_url,
    )


def build_kpay_provider(settings: Settings) -> KPayClient:
    return KPayClient(settings)


def _admin_payment_read(db: Session, item: ManualPayment) -> AdminPaymentRead:
    order = db.get(SubscriptionOrder, item.order_id)
    tenant = db.get(Tenant, item.tenant_id)
    store = db.get(Store, item.store_id)
    plan = db.get(SaasPlan, order.plan_id if order else None)
    assert order is not None and tenant is not None and store is not None and plan is not None
    return AdminPaymentRead(
        **_payment_read(db, item).model_dump(),
        tenant_name=tenant.name,
        store_name=store.name,
        plan_code=order.plan_code_snapshot or plan.code,
        product_family=order.product_family_snapshot or plan.product_family,
        order_status=order.status,
        submitted_at=item.submitted_at,
    )


def _product_subscription_read(db: Session, item: TenantSubscription) -> ProductSubscriptionRead:
    plan = db.get(SaasPlan, item.plan_id)
    assert plan is not None
    return ProductSubscriptionRead(
        product_family=item.product_family,
        active=True,
        subscription_public_id=item.public_id,
        plan_public_id=plan.public_id,
        plan_code=plan.code,
        source=item.source,
        status=item.status,
        limits=dict(item.limits_json or {}),
        starts_at=item.starts_at,
        current_period_end=item.current_period_end,
    )


def _admin_subscription_read(db: Session, item: TenantSubscription) -> AdminSubscriptionRead:
    tenant, store, plan = db.get(Tenant, item.tenant_id), db.get(Store, item.store_id), db.get(SaasPlan, item.plan_id)
    assert tenant is not None and store is not None and plan is not None
    return AdminSubscriptionRead(
        public_id=item.public_id, tenant_public_id=tenant.public_id,
        store_public_id=store.public_id, plan_public_id=plan.public_id,
        plan_code=plan.code, product_family=item.product_family,
        source=item.source, status=item.status, limits=dict(item.limits_json or {}),
        starts_at=item.starts_at, current_period_end=item.current_period_end,
    )


@router.get("/admin/commerce/plans", response_model=list[AdminPlanRead])
def admin_commerce_plans(
    _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_CATALOG_READ)),
    db: Session = Depends(get_db),
) -> list[AdminPlanRead]:
    return [AdminPlanRead.model_validate(item, from_attributes=True) for item in CommerceService(db).admin_plans()]


@router.post("/admin/commerce/plans", response_model=AdminPlanRead, status_code=201)
def admin_create_commerce_plan(
    payload: AdminPlanWrite,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_CATALOG_MANAGE)),
    db: Session = Depends(get_db),
) -> AdminPlanRead:
    try:
        item = CommerceService(db).admin_create_plan(actor_user_id=principal.user_id, **payload.model_dump())
        return AdminPlanRead.model_validate(item, from_attributes=True)
    except CommerceError as exc:
        _error(exc)


@router.patch("/admin/commerce/plans/{plan_public_id}", response_model=AdminPlanRead)
def admin_update_commerce_plan(
    plan_public_id: str,
    payload: AdminPlanUpdate,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_CATALOG_MANAGE)),
    db: Session = Depends(get_db),
) -> AdminPlanRead:
    values = payload.model_dump(exclude={"expected_revision"}, exclude_unset=True)
    try:
        item = CommerceService(db).admin_update_plan(plan_public_id, actor_user_id=principal.user_id, expected_revision=payload.expected_revision, **values)
        return AdminPlanRead.model_validate(item, from_attributes=True)
    except CommerceError as exc:
        _error(exc)


@router.get("/admin/commerce/subscriptions", response_model=list[AdminSubscriptionRead])
def admin_commerce_subscriptions(
    _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_SUBSCRIPTION_READ)),
    db: Session = Depends(get_db),
) -> list[AdminSubscriptionRead]:
    return [_admin_subscription_read(db, item) for item in CommerceService(db).admin_subscriptions()]


@router.get("/admin/commerce/customers", response_model=list[AdminCustomerStoreRead])
def admin_commerce_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_SUBSCRIPTION_READ)),
    db: Session = Depends(get_db),
) -> list[AdminCustomerStoreRead]:
    rows = db.execute(
        select(Tenant, Store)
        .join(Store, Store.tenant_id == Tenant.id)
        .order_by(Tenant.name, Store.name, Tenant.id, Store.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    capabilities_by_store = effective_capabilities_for_stores(
        db, stores=[store for _tenant, store in rows]
    )
    return [AdminCustomerStoreRead(
        tenant_public_id=tenant.public_id, tenant_name=tenant.name,
        store_public_id=store.public_id, store_name=store.name, store_status=store.status,
        effective_capabilities=list(capabilities_by_store[store.id]),
    ) for tenant, store in rows]


@router.get("/admin/commerce/audit", response_model=list[AdminCommerceAuditRead])
def admin_commerce_audit(
    action: str | None = None,
    target_type: str | None = None,
    target_public_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_CATALOG_READ)),
    db: Session = Depends(get_db),
) -> list[AdminCommerceAuditRead]:
    plan_query = select(CommerceAdminAuditLog)
    commerce_query = select(CommerceAuditLog).where(
        CommerceAuditLog.action.in_(("subscription.admin_granted", "subscription.admin_revoked"))
    )
    for column_name, value in (
        ("action", action),
        ("target_type", target_type),
        ("target_public_id", target_public_id),
    ):
        if value:
            plan_query = plan_query.where(getattr(CommerceAdminAuditLog, column_name) == value)
            commerce_query = commerce_query.where(getattr(CommerceAuditLog, column_name) == value)
    if created_from is not None:
        plan_query = plan_query.where(CommerceAdminAuditLog.created_at >= created_from)
        commerce_query = commerce_query.where(CommerceAuditLog.created_at >= created_from)
    if created_to is not None:
        plan_query = plan_query.where(CommerceAdminAuditLog.created_at <= created_to)
        commerce_query = commerce_query.where(CommerceAuditLog.created_at <= created_to)

    plan_rows = list(db.scalars(plan_query.order_by(CommerceAdminAuditLog.created_at.desc()).limit(limit)).all())
    commerce_rows = list(db.scalars(commerce_query.order_by(CommerceAuditLog.created_at.desc()).limit(limit)).all())
    actor_ids = {row.actor_user_id for row in [*plan_rows, *commerce_rows] if row.actor_user_id is not None}
    actors = {
        item.id: item
        for item in db.scalars(select(UserIdentity).where(UserIdentity.id.in_(actor_ids))).all()
    } if actor_ids else {}
    result: list[AdminCommerceAuditRead] = []
    for row in plan_rows:
        changes = dict(row.changes_json or {})
        actor = actors.get(row.actor_user_id)
        result.append(AdminCommerceAuditRead(
            source="commercial_policy", actor_display_name=actor.display_name if actor else None, action=row.action,
            target_type=row.target_type, target_public_id=row.target_public_id,
            changed_fields=list(changes.get("changed_fields") or changes.get("fields") or []),
            before=dict(changes.get("before") or {}), after=dict(changes.get("after") or {}),
            created_at=row.created_at,
        ))
    for row in commerce_rows:
        details = dict(row.details_json or {})
        actor = actors.get(row.actor_user_id) if row.actor_user_id is not None else None
        result.append(AdminCommerceAuditRead(
            source="subscription", actor_display_name=actor.display_name if actor else None, action=row.action,
            target_type=row.target_type, target_public_id=row.target_public_id,
            changed_fields=sorted(details), before={}, after=details, created_at=row.created_at,
        ))
    return sorted(result, key=lambda item: item.created_at, reverse=True)[:limit]


@router.post("/admin/commerce/subscriptions/grants", response_model=AdminSubscriptionRead, status_code=201)
def admin_grant_subscription(
    payload: AdminGrantCreate,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_SUBSCRIPTION_MANAGE)),
    db: Session = Depends(get_db),
) -> AdminSubscriptionRead:
    try:
        item = CommerceService(db).admin_grant(actor_user_id=principal.user_id, **payload.model_dump())
        return _admin_subscription_read(db, item)
    except CommerceError as exc:
        _error(exc)


@router.post("/admin/commerce/subscriptions/{subscription_public_id}/revoke", response_model=AdminSubscriptionRead)
def admin_revoke_subscription(
    subscription_public_id: str,
    _payload: AdminRevokeInput,
    principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.COMMERCE_SUBSCRIPTION_MANAGE)),
    db: Session = Depends(get_db),
) -> AdminSubscriptionRead:
    try:
        item = CommerceService(db).admin_revoke(subscription_public_id, actor_user_id=principal.user_id)
        return _admin_subscription_read(db, item)
    except CommerceError as exc:
        _error(exc)


def _subscription_read(db: Session, item: TenantSubscription) -> SubscriptionRead:
    tenant, store, plan = db.get(Tenant, item.tenant_id), db.get(Store, item.store_id), db.get(SaasPlan, item.plan_id)
    assert tenant is not None and store is not None and plan is not None
    effective = {sub.product_family: sub for sub in effective_product_subscriptions(
        db, tenant_id=tenant.id, store_id=store.id
    )}
    products = [
        _product_subscription_read(db, effective[family])
        if family in effective
        else ProductSubscriptionRead(product_family=family, active=False)
        for family in ("AUTOMATION", "AI_ASSISTANT")
    ]
    legacy = effective.get("LEGACY_BUNDLE")
    return SubscriptionRead(
        public_id=item.public_id,
        tenant_public_id=tenant.public_id,
        store_public_id=store.public_id,
        plan_public_id=plan.public_id,
        plan_code=plan.code,
        status=item.status,
        limits=dict(item.limits_json or {}),
        starts_at=item.starts_at,
        current_period_end=item.current_period_end,
        effective_capabilities=list(effective_capabilities(db, tenant_id=tenant.id, store_id=store.id)),
        products=products,
        legacy_bundle=_product_subscription_read(db, legacy) if legacy else None,
    )


@router.post("/payments/card-transfer", response_model=CardTransferInstructions, status_code=201)
def card_transfer(payload: CardTransferCreate, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> CardTransferInstructions:
    try:
        instructions = ManualCardTransferProvider(settings).instructions()
        payment = CommerceService(db).create_payment(principal, payload.order_public_id)
        return CardTransferInstructions(
            payment=_payment_read(db, payment),
            card_number=instructions.card_number,
            account_number=instructions.account_number,
            account_name=instructions.account_name,
            bank_name=instructions.bank_name,
            instructions=instructions.instructions,
        )
    except PaymentProviderUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "payment_provider_unavailable",
                "message": str(exc),
            },
        ) from exc
    except CommerceError as exc:
        _error(exc)


@router.post("/payments/kpay", response_model=KPayPaymentRead, status_code=201)
def create_kpay_payment(
    payload: KPayCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> KPayPaymentRead:
    provider = None
    try:
        if not settings.kpay_callback_base_url.startswith("https://"):
            raise KPayConfigurationError("KPay callback URL is not configured")
        provider = build_kpay_provider(settings)
        payment = CommerceService(db).create_kpay_payment(
            principal,
            payload.order_public_id,
            provider=provider,
            callback_base_url=settings.kpay_callback_base_url,
        )
        return _kpay_read(db, payment)
    except KPayConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "payment_provider_unavailable", "message": str(exc)},
        ) from exc
    except KPayProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "payment_provider_error", "message": str(exc)},
        ) from exc
    except CommerceError as exc:
        _error(exc)
    finally:
        if provider is not None:
            provider.close()


@router.get("/payments/kpay/{payment_public_id}", response_model=KPayPaymentRead)
def kpay_payment_status(
    payment_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> KPayPaymentRead:
    try:
        payment = CommerceService(db).get_owned_payment(principal, payment_public_id)
        if payment.provider != "kpay":
            raise CommerceNotFound("KPay payment not found")
        return _kpay_read(db, payment)
    except CommerceError as exc:
        _error(exc)


@router.get("/payments/kpay/callback/{payment_public_id}", include_in_schema=True)
def kpay_callback(
    payment_public_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    provider = None
    result = "pending"
    try:
        if not settings.kpay_callback_base_url.startswith("https://"):
            raise KPayConfigurationError("KPay callback URL is not configured")
        provider = build_kpay_provider(settings)
        payment = CommerceService(db).verify_kpay_payment(
            payment_public_id, provider=provider,
        )
        if payment.provider_operation_state == "PAID":
            result = "success"
        elif payment.provider_operation_state == "FAILED":
            result = "failed"
    except (KPayConfigurationError, KPayProviderError, CommerceError):
        # Browser callback parameters and provider error bodies are never
        # reflected. The authenticated result read remains authoritative.
        db.rollback()
        stored = db.scalar(
            select(ManualPayment).where(ManualPayment.public_id == payment_public_id)
        )
        result = (
            "failed"
            if stored is not None and stored.provider_operation_state == "FAILED"
            else "pending"
        )
    finally:
        if provider is not None:
            provider.close()
    location = (
        f"{settings.kpay_callback_base_url.rstrip('/')}/payment/result/"
        f"{payment_public_id}?result={result}"
    )
    return RedirectResponse(location, status_code=303)


@router.get("/payments/me", response_model=list[PaymentRead])
def my_payments(principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> list[PaymentRead]:
    try:
        return [_payment_read(db, item) for item in CommerceService(db).list_payments(principal)]
    except CommerceError as exc:
        _error(exc)


@router.post("/payments/{payment_public_id}/receipt", response_model=PaymentRead)
async def upload_receipt(payment_public_id: str, request: Request, principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> PaymentRead:
    chunks, total = [], 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > settings.receipt_max_bytes:
            raise HTTPException(status_code=413, detail={"code": "receipt_too_large", "message": "Receipt is too large"})
        chunks.append(chunk)
    service = CommerceService(db)
    stored = None
    storage = LocalPrivateReceiptStorage(settings.receipt_storage_root, max_bytes=settings.receipt_max_bytes)
    try:
        payment = service.get_owned_payment(principal, payment_public_id)
        tenant = db.get(Tenant, payment.tenant_id)
        assert tenant is not None
        stored = storage.store(tenant_public_id=tenant.public_id, payment_public_id=payment.public_id, content_type=request.headers.get("content-type", ""), data=b"".join(chunks))
        return _payment_read(db, service.submit_receipt(principal, payment_public_id, storage_key=stored.key, content_type=stored.content_type, size=stored.size, sha256=stored.sha256))
    except ReceiptValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_receipt", "message": str(exc)}) from exc
    except CommerceError as exc:
        if stored is not None:
            storage.delete(stored.key)
        _error(exc)


@router.get("/admin/payments", response_model=list[AdminPaymentRead])
def admin_payments(_principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_READ)), db: Session = Depends(get_db)) -> list[AdminPaymentRead]:
    return [_admin_payment_read(db, item) for item in CommerceService(db).admin_payments()]


@router.get("/admin/payments/{payment_public_id}", response_model=AdminPaymentRead)
def admin_payment(payment_public_id: str, _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_READ)), db: Session = Depends(get_db)) -> AdminPaymentRead:
    try:
        return _admin_payment_read(db, CommerceService(db).admin_payment(payment_public_id))
    except CommerceError as exc:
        _error(exc)


@router.post("/admin/payments/{payment_public_id}/approve", response_model=AdminPaymentRead)
def approve_payment(payment_public_id: str, payload: PaymentDecision, principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_MANAGE)), db: Session = Depends(get_db)) -> AdminPaymentRead:
    try:
        return _admin_payment_read(db, CommerceService(db).approve(payment_public_id, expected_revision=payload.expected_revision, actor_user_id=principal.user_id))
    except CommerceError as exc:
        _error(exc)


@router.post("/admin/payments/{payment_public_id}/reject", response_model=AdminPaymentRead)
def reject_payment(payment_public_id: str, payload: PaymentDecision, principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_MANAGE)), db: Session = Depends(get_db)) -> AdminPaymentRead:
    try:
        return _admin_payment_read(db, CommerceService(db).reject(payment_public_id, expected_revision=payload.expected_revision, actor_user_id=principal.user_id, reason=payload.reason))
    except CommerceError as exc:
        _error(exc)


@router.get("/admin/payments/{payment_public_id}/receipt", response_class=FileResponse)
def admin_receipt(payment_public_id: str, _principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_READ)), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> FileResponse:
    try:
        payment = CommerceService(db).admin_payment(payment_public_id)
        if not payment.receipt_storage_key:
            raise CommerceNotFound("receipt not found")
        root = Path(settings.receipt_storage_root).resolve()
        path = (root / payment.receipt_storage_key).resolve()
        if root not in path.parents or not path.is_file():
            raise CommerceNotFound("receipt not found")
        return FileResponse(path, media_type=payment.receipt_content_type, filename=f"receipt-{payment.public_id}{path.suffix}")
    except CommerceError as exc:
        _error(exc)


@router.get("/subscription/me", response_model=SubscriptionRead | None)
def my_subscription(principal: AuthenticatedPrincipal = Depends(require_authenticated_principal), db: Session = Depends(get_db)) -> SubscriptionRead | None:
    try:
        item = CommerceService(db).subscription(principal)
        if item is None:
            return None
        return _subscription_read(db, item)
    except CommerceError as exc:
        _error(exc)


@router.post("/subscription/me/reconcile-capabilities", response_model=SubscriptionRead)
def reconcile_my_subscription_capabilities(
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> SubscriptionRead:
    try:
        CommerceService(db).reconcile_subscription_modules(principal)
        item = CommerceService(db).subscription(principal)
        assert item is not None
        return _subscription_read(db, item)
    except CommerceError as exc:
        _error(exc)
