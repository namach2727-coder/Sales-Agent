"""Customer and provider HTTP adapters for the sellable SaaS MVP."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import build_authentication_service, require_authenticated_principal, require_platform_permission
from app.authentication.exceptions import AuthenticationError, AuthenticationValidationError
from app.authentication.passwords import PasswordService
from app.authentication.schemas import LoginInput
from app.authz.permissions import PermissionCode
from app.commerce.schemas import (
    CardTransferCreate,
    CardTransferInstructions,
    OrderCreate,
    OrderRead,
    PaymentDecision,
    PaymentRead,
    PlanRead,
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
from app.commerce.service import CommerceConflict, CommerceError, CommerceForbidden, CommerceNotFound, CommerceService, RegistrationService
from app.commerce.storage import LocalPrivateReceiptStorage, ReceiptValidationError
from app.config import Settings, get_settings
from app.database import get_db
from app.models import ManualPayment, SaasPlan, Store, SubscriptionOrder, Tenant, TenantSubscription
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
    return PublicPrincipal(email=principal.email, display_name=principal.display_name, session_public_id=principal.session_id, authenticated_at=principal.authenticated_at, tenant_memberships=memberships)


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
    return OrderRead(public_id=item.public_id, tenant_public_id=tenant.public_id, store_public_id=store.public_id, plan_public_id=plan.public_id, plan_code=plan.code, status=item.status, price_amount=item.price_amount, currency=item.currency, created_at=item.created_at)


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


@router.get("/admin/payments", response_model=list[PaymentRead])
def admin_payments(_principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_READ)), db: Session = Depends(get_db)) -> list[PaymentRead]:
    return [_payment_read(db, item) for item in CommerceService(db).admin_payments()]


@router.post("/admin/payments/{payment_public_id}/approve", response_model=PaymentRead)
def approve_payment(payment_public_id: str, payload: PaymentDecision, principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_MANAGE)), db: Session = Depends(get_db)) -> PaymentRead:
    try:
        return _payment_read(db, CommerceService(db).approve(payment_public_id, expected_revision=payload.expected_revision, actor_user_id=principal.user_id))
    except CommerceError as exc:
        _error(exc)


@router.post("/admin/payments/{payment_public_id}/reject", response_model=PaymentRead)
def reject_payment(payment_public_id: str, payload: PaymentDecision, principal: AuthenticatedPrincipal = Depends(require_platform_permission(PermissionCode.PAYMENT_MANAGE)), db: Session = Depends(get_db)) -> PaymentRead:
    try:
        return _payment_read(db, CommerceService(db).reject(payment_public_id, expected_revision=payload.expected_revision, actor_user_id=principal.user_id, reason=payload.reason))
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
        tenant, store, plan = db.get(Tenant, item.tenant_id), db.get(Store, item.store_id), db.get(SaasPlan, item.plan_id)
        assert tenant is not None and store is not None and plan is not None
        return SubscriptionRead(public_id=item.public_id, tenant_public_id=tenant.public_id, store_public_id=store.public_id, plan_public_id=plan.public_id, plan_code=plan.code, status=item.status, limits=dict(item.limits_json or {}), starts_at=item.starts_at, current_period_end=item.current_period_end)
    except CommerceError as exc:
        _error(exc)
