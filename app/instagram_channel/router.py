"""Authenticated management and public Meta webhook routes."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_channel.exceptions import (
    InstagramChannelConflictError,
    InstagramChannelError,
    InstagramChannelInvalidTransitionError,
    InstagramChannelNotFoundError,
    InstagramChannelScopeError,
    InstagramChannelStaleWriteError,
    InstagramChannelValidationError,
    InstagramCredentialConfigurationError,
    InstagramWebhookPayloadError,
    InstagramWebhookSecurityError,
)
from app.instagram_channel.schemas import (
    EventType,
    InstagramConnectionAction,
    InstagramConnectionCreate,
    InstagramConnectionPage,
    InstagramConnectionRead,
    InstagramConnectionUpdate,
    InstagramInboundEventPage,
    InstagramInboundEventRead,
    InstagramTokenRotate,
    InstagramWebhookDeliveryPage,
    InstagramWebhookDeliveryRead,
    InstagramWebhookReceipt,
)
from app.instagram_channel.security import (
    FernetTokenCipher,
    verify_meta_signature,
    verify_subscription,
)
from app.instagram_channel.service import (
    InstagramChannelService,
    InstagramWebhookIngestionService,
    connection_to_public,
)
from app.observability import correlation_id
from app.tenant_management.context import (
    TenantStoreContext,
    resolve_authorized_context,
)
from app.tenant_management.domain import TenantManagementError


logger = logging.getLogger("sales_assistant.instagram_channel.router")

router = APIRouter(
    prefix=(
        "/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}"
        "/instagram-channel"
    ),
    tags=["instagram-channel"],
)
public_router = APIRouter(tags=["instagram-channel-public"])


def _raise(error: Exception) -> None:
    if isinstance(error, InstagramChannelValidationError):
        raise HTTPException(
            status_code=422,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, InstagramChannelStaleWriteError):
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(
        error,
        (InstagramChannelConflictError, InstagramChannelInvalidTransitionError),
    ):
        raise HTTPException(
            status_code=409,
            detail={"code": error.code, "message": str(error)},
        )
    if isinstance(error, InstagramCredentialConfigurationError):
        raise HTTPException(
            status_code=503,
            detail={"code": error.code, "message": "Credential service unavailable"},
        )
    if isinstance(error, InstagramChannelScopeError):
        raise HTTPException(
            status_code=403,
            detail={"code": error.code, "message": "Permission denied"},
        )
    if isinstance(error, (InstagramChannelNotFoundError, TenantManagementError)):
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        )
    raise error


def _service(
    tenant_public_id: str,
    store_public_id: str,
    permission: str,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    mutation: bool,
) -> tuple[InstagramChannelService, TenantStoreContext]:
    try:
        context = resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            tenant_permission=permission,
            store_permission=permission,
            platform_permission=(
                PermissionCode.TENANT_UPDATE
                if mutation
                else PermissionCode.TENANT_READ
            ),
            operational=False,
        )
    except TenantManagementError as exc:
        _raise(exc)
    assert context.store_id is not None and context.store_status is not None
    return (
        InstagramChannelService(
            db,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
            tenant_status=context.tenant_status,
            store_status=context.store_status,
            actor_identity_id=principal.user_id,
        ),
        context,
    )


@public_router.get(
    "/api/v1/integrations/instagram/webhook",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
def verify_instagram_subscription(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    settings: Settings = Depends(get_settings),
) -> str:
    try:
        return verify_subscription(
            mode=hub_mode,
            challenge=hub_challenge,
            supplied_token=hub_verify_token,
            configured_token=settings.meta_verify_token,
        )
    except InstagramWebhookSecurityError as exc:
        logger.warning(
            "Instagram webhook verification rejected",
            extra={"event_code": "instagram.webhook.verification_rejected"},
        )
        status_code = 503 if not settings.meta_verify_token.strip() else 403
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": "webhook_verification_failed",
                "message": "Webhook verification failed",
            },
        ) from exc


@public_router.post(
    "/api/v1/integrations/instagram/webhook",
    response_model=InstagramWebhookReceipt,
    include_in_schema=False,
)
async def receive_instagram_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    try:
        verify_meta_signature(raw_body, signature, settings.meta_app_secret)
    except InstagramWebhookSecurityError as exc:
        logger.warning(
            "Instagram webhook signature rejected",
            extra={"event_code": "instagram.webhook.signature_rejected"},
        )
        status_code = 503 if not settings.meta_app_secret.strip() else 401
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": "invalid_webhook_signature",
                "message": "Webhook signature validation failed",
            },
        ) from exc
    try:
        payload = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning(
            "Instagram webhook JSON rejected",
            extra={"event_code": "instagram.webhook.invalid_json"},
        )
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_webhook_payload",
                "message": "Webhook payload is invalid",
            },
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_webhook_payload",
                "message": "Webhook payload is invalid",
            },
        )
    external_delivery_key = (
        request.headers.get("x-hub-delivery")
        or request.headers.get("x-meta-delivery-id")
    )
    try:
        receipt, duplicate, event_count = InstagramWebhookIngestionService(
            db
        ).ingest(
            raw_body=raw_body,
            payload=payload,
            external_delivery_key=external_delivery_key,
            correlation_id=correlation_id.get(),
        )
    except InstagramWebhookPayloadError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.code,
                "message": "Webhook payload is invalid",
            },
        ) from exc
    except InstagramChannelError as exc:
        logger.error(
            "Instagram webhook processing failed",
            extra={"event_code": "instagram.webhook.processing_failed"},
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "webhook_processing_failed",
                "message": "Webhook processing failed",
            },
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(
            "Instagram webhook processing failed unexpectedly",
            extra={"event_code": "instagram.webhook.processing_failed"},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "code": "webhook_processing_failed",
                "message": "Webhook processing failed",
            },
        ) from exc
    return {
        "status": receipt,
        "duplicate": duplicate,
        "event_count": event_count,
    }


@router.post(
    "/connections",
    response_model=InstagramConnectionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_connection(
    tenant_public_id: str,
    store_public_id: str,
    payload: InstagramConnectionCreate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_CONNECTION_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return connection_to_public(
            service.create_connection(**payload.model_dump())
        )
    except InstagramChannelError as exc:
        _raise(exc)


@router.get("/connections", response_model=InstagramConnectionPage)
def list_connections(
    tenant_public_id: str,
    store_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_CONNECTION_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_connections(page=page, page_size=page_size)
        return {
            "items": [connection_to_public(item) for item in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except InstagramChannelError as exc:
        _raise(exc)


@router.get(
    "/connections/{connection_public_id}",
    response_model=InstagramConnectionRead,
)
def read_connection(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_CONNECTION_READ,
            principal,
            db,
            mutation=False,
        )
        return connection_to_public(service.get_connection(connection_public_id))
    except InstagramChannelError as exc:
        _raise(exc)


@router.patch(
    "/connections/{connection_public_id}",
    response_model=InstagramConnectionRead,
)
def update_connection(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramConnectionUpdate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_CONNECTION_MANAGE,
            principal,
            db,
            mutation=True,
        )
        return connection_to_public(
            service.update_connection(
                connection_public_id,
                expected_revision=payload.expected_revision,
                changes=payload.model_dump(
                    exclude_unset=True, exclude={"expected_revision"}
                ),
            )
        )
    except InstagramChannelError as exc:
        _raise(exc)


@router.post(
    "/connections/{connection_public_id}/token",
    response_model=InstagramConnectionRead,
)
def rotate_connection_token(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramTokenRotate,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_CONNECTION_CREDENTIALS_MANAGE,
            principal,
            db,
            mutation=True,
        )
        cipher = FernetTokenCipher.from_settings(settings)
        return connection_to_public(
            service.rotate_token(
                connection_public_id,
                expected_revision=payload.expected_revision,
                access_token=payload.access_token.get_secret_value(),
                token_type=payload.token_type,
                token_expires_at=payload.token_expires_at,
                scopes=payload.scopes,
                cipher=cipher,
            )
        )
    except InstagramChannelError as exc:
        _raise(exc)


def _connection_action(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramConnectionAction,
    principal: AuthenticatedPrincipal,
    db: Session,
    *,
    action: str,
) -> dict[str, object]:
    service, _ = _service(
        tenant_public_id,
        store_public_id,
        PermissionCode.INSTAGRAM_CONNECTION_MANAGE,
        principal,
        db,
        mutation=True,
    )
    method = getattr(service, action)
    return connection_to_public(
        method(
            connection_public_id,
            expected_revision=payload.expected_revision,
            reason=payload.reason,
        )
    )


@router.post(
    "/connections/{connection_public_id}/activate",
    response_model=InstagramConnectionRead,
)
def activate_connection(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramConnectionAction,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return _connection_action(
            tenant_public_id,
            store_public_id,
            connection_public_id,
            payload,
            principal,
            db,
            action="activate",
        )
    except InstagramChannelError as exc:
        _raise(exc)


@router.post(
    "/connections/{connection_public_id}/disconnect",
    response_model=InstagramConnectionRead,
)
def disconnect_connection(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramConnectionAction,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return _connection_action(
            tenant_public_id,
            store_public_id,
            connection_public_id,
            payload,
            principal,
            db,
            action="disconnect",
        )
    except InstagramChannelError as exc:
        _raise(exc)


@router.post(
    "/connections/{connection_public_id}/archive",
    response_model=InstagramConnectionRead,
)
def archive_connection(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    payload: InstagramConnectionAction,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return _connection_action(
            tenant_public_id,
            store_public_id,
            connection_public_id,
            payload,
            principal,
            db,
            action="archive",
        )
    except InstagramChannelError as exc:
        _raise(exc)


@router.get(
    "/connections/{connection_public_id}/deliveries",
    response_model=InstagramWebhookDeliveryPage,
)
def list_deliveries(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_WEBHOOK_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_deliveries(
            connection_public_id, page=page, page_size=page_size
        )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except InstagramChannelError as exc:
        _raise(exc)


@router.get(
    "/connections/{connection_public_id}/deliveries/{delivery_public_id}",
    response_model=InstagramWebhookDeliveryRead,
)
def read_delivery(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    delivery_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
):
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_WEBHOOK_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_delivery(connection_public_id, delivery_public_id)
    except InstagramChannelError as exc:
        _raise(exc)


@router.get(
    "/connections/{connection_public_id}/events",
    response_model=InstagramInboundEventPage,
)
def list_events(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    event_type: EventType | None = Query(default=None),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_EVENT_READ,
            principal,
            db,
            mutation=False,
        )
        items, total = service.list_events(
            connection_public_id,
            page=page,
            page_size=page_size,
            event_type=event_type,
        )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    except InstagramChannelError as exc:
        _raise(exc)


@router.get(
    "/connections/{connection_public_id}/events/{event_public_id}",
    response_model=InstagramInboundEventRead,
)
def read_event(
    tenant_public_id: str,
    store_public_id: str,
    connection_public_id: str,
    event_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
):
    try:
        service, _ = _service(
            tenant_public_id,
            store_public_id,
            PermissionCode.INSTAGRAM_EVENT_READ,
            principal,
            db,
            mutation=False,
        )
        return service.get_event(connection_public_id, event_public_id)
    except InstagramChannelError as exc:
        _raise(exc)
