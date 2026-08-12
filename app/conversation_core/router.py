"""Authenticated read-only customer inbox API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.services import ConversationService
from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode
from app.conversation_core.exceptions import ConversationNotFoundError
from app.conversation_core.models import Conversation, ConversationMessage, ConversationParticipant
from app.conversation_core.schemas import (
    ConversationMessagePage,
    ConversationMessageRead,
    ConversationPage,
    ConversationRead,
)
from app.database import get_db
from app.infrastructure.database.repositories import ConversationRepository, MessageRepository
from app.tenant_management.context import TenantStoreContext, resolve_authorized_context
from app.tenant_management.domain import TenantManagementError


router = APIRouter(
    prefix="/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/inbox",
    tags=["customer-inbox"],
)


def _context(
    db: Session,
    principal: AuthenticatedPrincipal,
    tenant_public_id: str,
    store_public_id: str,
) -> TenantStoreContext:
    try:
        return resolve_authorized_context(
            db,
            principal,
            tenant_public_id=tenant_public_id,
            store_public_id=store_public_id,
            tenant_permission=PermissionCode.CONVERSATION_READ,
            store_permission=PermissionCode.CONVERSATION_READ,
            platform_permission=PermissionCode.TENANT_READ,
            operational=False,
        )
    except TenantManagementError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        ) from exc


def _participant(db: Session, conversation: Conversation) -> tuple[str | None, str | None]:
    item = db.scalar(
        select(ConversationParticipant)
        .where(
            ConversationParticipant.tenant_id == conversation.tenant_id,
            ConversationParticipant.store_id == conversation.store_id,
            ConversationParticipant.conversation_id == conversation.id,
            ConversationParticipant.participant_type == "customer",
            ConversationParticipant.left_at.is_(None),
        )
        .order_by(ConversationParticipant.joined_at, ConversationParticipant.id)
        .limit(1)
    )
    return (
        (item.display_name, item.username) if item is not None else (None, None)
    )


def _conversation_read(db: Session, item: Conversation) -> ConversationRead:
    display_name, username = _participant(db, item)
    return ConversationRead(
        public_id=item.public_id,
        status=item.status,
        subject=item.subject,
        participant_display_name=display_name,
        participant_username=username,
        last_message_at=item.last_message_at,
        last_inbound_message_at=item.last_inbound_message_at,
        last_outbound_message_at=item.last_outbound_message_at,
        message_count=item.message_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _message_read(item: ConversationMessage) -> ConversationMessageRead:
    delivery = (item.metadata_json or {}).get("delivery_status")
    return ConversationMessageRead(
        public_id=item.public_id,
        direction=item.direction,
        role=(
            "customer"
            if item.direction == "inbound"
            else "assistant"
            if item.direction == "outbound"
            else "system"
        ),
        content_type=item.content_type,
        content=item.text,
        delivery_status=delivery if isinstance(delivery, str) else None,
        occurred_at=item.occurred_at,
        created_at=item.created_at,
    )


@router.get("/conversations", response_model=ConversationPage)
def list_conversations(
    tenant_public_id: str,
    store_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ConversationPage:
    context = _context(db, principal, tenant_public_id, store_public_id)
    assert context.store_id is not None
    items, total = ConversationRepository(db).page_by_store(
        tenant_id=context.tenant_id,
        store_id=context.store_id,
        page=page,
        page_size=page_size,
    )
    return ConversationPage(
        items=[_conversation_read(db, item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/conversations/{conversation_public_id}", response_model=ConversationRead)
def read_conversation(
    tenant_public_id: str,
    store_public_id: str,
    conversation_public_id: str,
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ConversationRead:
    context = _context(db, principal, tenant_public_id, store_public_id)
    assert context.store_id is not None
    try:
        item = ConversationService(
            ConversationRepository(db), MessageRepository(db)
        ).get_conversation(
            conversation_public_id,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        ) from exc
    return _conversation_read(db, item)


@router.get(
    "/conversations/{conversation_public_id}/messages",
    response_model=ConversationMessagePage,
)
def list_conversation_messages(
    tenant_public_id: str,
    store_public_id: str,
    conversation_public_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
    db: Session = Depends(get_db),
) -> ConversationMessagePage:
    context = _context(db, principal, tenant_public_id, store_public_id)
    assert context.store_id is not None
    service = ConversationService(ConversationRepository(db), MessageRepository(db))
    try:
        conversation = service.get_conversation(
            conversation_public_id,
            tenant_id=context.tenant_id,
            store_id=context.store_id,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resource not found"},
        ) from exc
    items, total = MessageRepository(db).page_by_conversation(
        conversation.id,
        tenant_id=context.tenant_id,
        store_id=context.store_id,
        page=page,
        page_size=page_size,
    )
    return ConversationMessagePage(
        items=[_message_read(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )
