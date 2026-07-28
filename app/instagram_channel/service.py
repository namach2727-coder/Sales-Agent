"""Connection lifecycle, diagnostics, and transactional webhook ingestion."""

from __future__ import annotations

from datetime import datetime
import logging
from time import monotonic
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.instagram_channel.domain import (
    READABLE_STORE_STATUSES,
    ROUTABLE_CONNECTION_STATUSES,
    WRITABLE_STORE_STATUSES,
    canonical_payload_hash,
    normalize_identifier,
    normalize_optional_text,
    normalize_scopes,
    parse_instagram_webhook,
    validate_transition,
)
from app.instagram_channel.exceptions import (
    InstagramChannelConflictError,
    InstagramChannelNotFoundError,
    InstagramChannelScopeError,
    InstagramChannelStaleWriteError,
    InstagramChannelValidationError,
    InstagramWebhookPayloadError,
)
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
    InstagramWebhookDelivery,
)
from app.instagram_channel.security import TokenCipher
from app.models import TenantAuditLog, utc_now


logger = logging.getLogger("sales_assistant.instagram_channel")


def connection_to_public(item: InstagramConnection) -> dict[str, object]:
    return {
        "public_id": item.public_id,
        "meta_app_id": item.meta_app_id,
        "facebook_page_id": item.facebook_page_id,
        "instagram_account_id": item.instagram_account_id,
        "instagram_username": item.instagram_username,
        "external_account_name": item.external_account_name,
        "status": item.status,
        "status_reason": item.status_reason,
        "connected_at": item.connected_at,
        "disconnected_at": item.disconnected_at,
        "last_verified_at": item.last_verified_at,
        "last_webhook_received_at": item.last_webhook_received_at,
        "token_configured": item.encrypted_access_token is not None,
        "token_type": item.token_type,
        "token_expires_at": item.token_expires_at,
        "token_scopes": item.token_scopes,
        "token_updated_at": item.token_updated_at,
        "revision": item.revision,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "archived_at": item.archived_at,
    }


class InstagramChannelService:
    def __init__(
        self,
        session: Session,
        *,
        tenant_id: int,
        store_id: int,
        tenant_status: str,
        store_status: str,
        actor_identity_id: int | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.store_id = store_id
        self.tenant_status = tenant_status
        self.store_status = store_status
        self.actor_identity_id = actor_identity_id

    def _ensure_readable(self) -> None:
        if self.tenant_status != "active":
            raise InstagramChannelScopeError("tenant is not active")
        if self.store_status in {"archived", "deleted"}:
            raise InstagramChannelNotFoundError("resource not found")
        if self.store_status not in READABLE_STORE_STATUSES:
            raise InstagramChannelScopeError("store is not readable")

    def _ensure_writable(self) -> None:
        self._ensure_readable()
        if self.store_status not in WRITABLE_STORE_STATUSES:
            raise InstagramChannelScopeError("store is not writable")

    def _audit(
        self,
        *,
        action: str,
        connection_public_id: str,
        details: dict[str, object],
    ) -> None:
        self.session.add(
            TenantAuditLog(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                actor_identity_id=self.actor_identity_id,
                action=action,
                target_type="instagram_connection",
                target_public_id=connection_public_id,
                details_json=details,
            )
        )

    def _commit(self, conflict_message: str = "Instagram connection conflict") -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise InstagramChannelConflictError(conflict_message) from exc
        except StaleDataError as exc:
            self.session.rollback()
            raise InstagramChannelStaleWriteError(
                "resource was changed by another request"
            ) from exc

    def _connection(self, public_id: str) -> InstagramConnection:
        self._ensure_readable()
        item = self.session.scalar(
            select(InstagramConnection).where(
                InstagramConnection.public_id == public_id,
                InstagramConnection.tenant_id == self.tenant_id,
                InstagramConnection.store_id == self.store_id,
            )
        )
        if item is None:
            raise InstagramChannelNotFoundError("resource not found")
        return item

    @staticmethod
    def _check_revision(item: InstagramConnection, expected_revision: int) -> None:
        if item.revision != expected_revision:
            raise InstagramChannelStaleWriteError(
                "resource was changed by another request"
            )

    @staticmethod
    def _ensure_mutable(item: InstagramConnection) -> None:
        if item.status == "archived":
            raise InstagramChannelConflictError(
                "archived connection cannot be changed"
            )

    def create_connection(
        self,
        *,
        expected_revision: int,
        meta_app_id: str | None,
        facebook_page_id: str | None,
        instagram_account_id: str,
        instagram_username: str | None,
        external_account_name: str | None,
    ) -> InstagramConnection:
        self._ensure_writable()
        if expected_revision != 0:
            raise InstagramChannelValidationError(
                "expected_revision must be zero for create"
            )
        item = InstagramConnection(
            tenant_id=self.tenant_id,
            store_id=self.store_id,
            meta_app_id=normalize_identifier(
                meta_app_id, field="Meta app ID", maximum=100
            ),
            facebook_page_id=normalize_identifier(
                facebook_page_id, field="Facebook page ID"
            ),
            instagram_account_id=normalize_identifier(
                instagram_account_id,
                field="Instagram account ID",
                required=True,
            ),
            instagram_username=normalize_identifier(
                instagram_username, field="Instagram username", maximum=100
            ),
            external_account_name=normalize_optional_text(
                external_account_name,
                field="external account name",
                maximum=200,
            ),
            status="pending",
            token_scopes=[],
        )
        self.session.add(item)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise InstagramChannelConflictError(
                "Instagram account or store connection already exists"
            ) from exc
        self._audit(
            action="instagram.connection.created",
            connection_public_id=item.public_id,
            details={"status": item.status},
        )
        self._commit("Instagram account or store connection already exists")
        self.session.refresh(item)
        return item

    def list_connections(
        self, *, page: int, page_size: int
    ) -> tuple[list[InstagramConnection], int]:
        self._ensure_readable()
        criteria = (
            InstagramConnection.tenant_id == self.tenant_id,
            InstagramConnection.store_id == self.store_id,
        )
        total = self.session.scalar(
            select(func.count()).select_from(InstagramConnection).where(*criteria)
        )
        items = list(
            self.session.scalars(
                select(InstagramConnection)
                .where(*criteria)
                .order_by(
                    InstagramConnection.created_at.desc(),
                    InstagramConnection.public_id,
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, int(total or 0)

    def get_connection(self, public_id: str) -> InstagramConnection:
        return self._connection(public_id)

    def update_connection(
        self,
        public_id: str,
        *,
        expected_revision: int,
        changes: dict[str, object],
    ) -> InstagramConnection:
        self._ensure_writable()
        item = self._connection(public_id)
        self._ensure_mutable(item)
        self._check_revision(item, expected_revision)
        normalizers = {
            "meta_app_id": lambda value: normalize_identifier(
                value, field="Meta app ID", maximum=100
            ),
            "facebook_page_id": lambda value: normalize_identifier(
                value, field="Facebook page ID"
            ),
            "instagram_account_id": lambda value: normalize_identifier(
                value,
                field="Instagram account ID",
                required=True,
            ),
            "instagram_username": lambda value: normalize_identifier(
                value, field="Instagram username", maximum=100
            ),
            "external_account_name": lambda value: normalize_optional_text(
                value, field="external account name", maximum=200
            ),
            "status_reason": lambda value: normalize_optional_text(
                value, field="status reason", maximum=500
            ),
        }
        changed_fields: list[str] = []
        for name, value in changes.items():
            normalized = normalizers[name](value)
            if getattr(item, name) != normalized:
                setattr(item, name, normalized)
                changed_fields.append(name)
        if changed_fields:
            item.revision += 1
            item.updated_at = utc_now()
            self._audit(
                action="instagram.connection.updated",
                connection_public_id=item.public_id,
                details={"changed_fields": sorted(changed_fields)},
            )
            self._commit("Instagram account identifier already exists")
            self.session.refresh(item)
        return item

    def rotate_token(
        self,
        public_id: str,
        *,
        expected_revision: int,
        access_token: str,
        token_type: str | None,
        token_expires_at: datetime | None,
        scopes: list[str],
        cipher: TokenCipher,
    ) -> InstagramConnection:
        self._ensure_writable()
        item = self._connection(public_id)
        self._ensure_mutable(item)
        self._check_revision(item, expected_revision)
        encrypted = cipher.encrypt(access_token)
        item.encrypted_access_token = encrypted
        item.token_type = normalize_identifier(
            token_type, field="token type", maximum=50
        )
        item.token_expires_at = token_expires_at
        item.token_scopes = normalize_scopes(scopes)
        item.token_updated_at = utc_now()
        item.revision += 1
        item.updated_at = utc_now()
        self._audit(
            action="instagram.connection.credential_rotated",
            connection_public_id=item.public_id,
            details={
                "token_configured": True,
                "token_type": item.token_type,
                "token_expires_at": (
                    item.token_expires_at.isoformat()
                    if item.token_expires_at is not None
                    else None
                ),
                "scope_count": len(item.token_scopes),
            },
        )
        self._commit()
        self.session.refresh(item)
        return item

    def activate(
        self,
        public_id: str,
        *,
        expected_revision: int,
        reason: str | None,
    ) -> InstagramConnection:
        self._ensure_writable()
        item = self._connection(public_id)
        self._ensure_mutable(item)
        self._check_revision(item, expected_revision)
        if item.encrypted_access_token is None:
            raise InstagramChannelConflictError(
                "connection credentials must be configured before activation"
            )
        validate_transition(item.status, "active")
        now = utc_now()
        item.status = "active"
        item.status_reason = normalize_optional_text(
            reason, field="reason", maximum=500
        )
        item.connected_at = item.connected_at or now
        item.disconnected_at = None
        item.last_verified_at = now
        item.archived_at = None
        item.revision += 1
        item.updated_at = now
        self._audit(
            action="instagram.connection.activated",
            connection_public_id=item.public_id,
            details={"status": "active", "verification": "local_readiness"},
        )
        self._commit()
        self.session.refresh(item)
        return item

    def disconnect(
        self,
        public_id: str,
        *,
        expected_revision: int,
        reason: str | None,
    ) -> InstagramConnection:
        return self._transition(
            public_id,
            expected_revision=expected_revision,
            target="disconnected",
            reason=reason,
            action="instagram.connection.disconnected",
        )

    def archive(
        self,
        public_id: str,
        *,
        expected_revision: int,
        reason: str | None,
    ) -> InstagramConnection:
        return self._transition(
            public_id,
            expected_revision=expected_revision,
            target="archived",
            reason=reason,
            action="instagram.connection.archived",
        )

    def _transition(
        self,
        public_id: str,
        *,
        expected_revision: int,
        target: str,
        reason: str | None,
        action: str,
    ) -> InstagramConnection:
        self._ensure_writable()
        item = self._connection(public_id)
        self._ensure_mutable(item)
        self._check_revision(item, expected_revision)
        validate_transition(item.status, target)
        now = utc_now()
        item.status = target
        item.status_reason = normalize_optional_text(
            reason, field="reason", maximum=500
        )
        if target in {"disconnected", "revoked"}:
            item.disconnected_at = now
        if target == "archived":
            item.archived_at = now
        item.revision += 1
        item.updated_at = now
        self._audit(
            action=action,
            connection_public_id=item.public_id,
            details={"status": target},
        )
        self._commit()
        self.session.refresh(item)
        return item

    def list_deliveries(
        self,
        connection_public_id: str,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[InstagramWebhookDelivery], int]:
        connection = self._connection(connection_public_id)
        criteria = (
            InstagramWebhookDelivery.tenant_id == self.tenant_id,
            InstagramWebhookDelivery.store_id == self.store_id,
            InstagramWebhookDelivery.instagram_connection_id == connection.id,
        )
        total = self.session.scalar(
            select(func.count())
            .select_from(InstagramWebhookDelivery)
            .where(*criteria)
        )
        items = list(
            self.session.scalars(
                select(InstagramWebhookDelivery)
                .where(*criteria)
                .order_by(
                    InstagramWebhookDelivery.received_at.desc(),
                    InstagramWebhookDelivery.public_id,
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, int(total or 0)

    def get_delivery(
        self, connection_public_id: str, delivery_public_id: str
    ) -> InstagramWebhookDelivery:
        connection = self._connection(connection_public_id)
        item = self.session.scalar(
            select(InstagramWebhookDelivery).where(
                InstagramWebhookDelivery.public_id == delivery_public_id,
                InstagramWebhookDelivery.tenant_id == self.tenant_id,
                InstagramWebhookDelivery.store_id == self.store_id,
                InstagramWebhookDelivery.instagram_connection_id == connection.id,
            )
        )
        if item is None:
            raise InstagramChannelNotFoundError("resource not found")
        return item

    def list_events(
        self,
        connection_public_id: str,
        *,
        page: int,
        page_size: int,
        event_type: str | None,
    ) -> tuple[list[InstagramInboundEvent], int]:
        connection = self._connection(connection_public_id)
        criteria: list[Any] = [
            InstagramInboundEvent.tenant_id == self.tenant_id,
            InstagramInboundEvent.store_id == self.store_id,
            InstagramInboundEvent.instagram_connection_id == connection.id,
        ]
        if event_type is not None:
            criteria.append(InstagramInboundEvent.event_type == event_type)
        total = self.session.scalar(
            select(func.count()).select_from(InstagramInboundEvent).where(*criteria)
        )
        items = list(
            self.session.scalars(
                select(InstagramInboundEvent)
                .where(*criteria)
                .order_by(
                    InstagramInboundEvent.received_at.desc(),
                    InstagramInboundEvent.public_id,
                )
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, int(total or 0)

    def get_event(
        self, connection_public_id: str, event_public_id: str
    ) -> InstagramInboundEvent:
        connection = self._connection(connection_public_id)
        item = self.session.scalar(
            select(InstagramInboundEvent).where(
                InstagramInboundEvent.public_id == event_public_id,
                InstagramInboundEvent.tenant_id == self.tenant_id,
                InstagramInboundEvent.store_id == self.store_id,
                InstagramInboundEvent.instagram_connection_id == connection.id,
            )
        )
        if item is None:
            raise InstagramChannelNotFoundError("resource not found")
        return item


class InstagramWebhookIngestionService:
    """Persist one verified Meta delivery and normalize its routed events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _find_duplicate(
        self,
        *,
        external_delivery_key: str | None,
        payload_hash: str,
    ) -> InstagramWebhookDelivery | None:
        criteria = [InstagramWebhookDelivery.provider == "meta"]
        if external_delivery_key is not None:
            criteria.append(
                or_(
                    InstagramWebhookDelivery.external_delivery_key
                    == external_delivery_key,
                    InstagramWebhookDelivery.payload_hash == payload_hash,
                )
            )
        else:
            criteria.append(InstagramWebhookDelivery.payload_hash == payload_hash)
        return self.session.scalar(
            select(InstagramWebhookDelivery).where(*criteria)
        )

    def _audit_delivery(
        self,
        delivery: InstagramWebhookDelivery,
        *,
        action: str,
        details: dict[str, object],
    ) -> None:
        if (
            delivery.tenant_id is None
            or delivery.store_id is None
            or delivery.instagram_connection_id is None
        ):
            return
        connection = self.session.get(
            InstagramConnection, delivery.instagram_connection_id
        )
        if connection is None:
            return
        self.session.add(
            TenantAuditLog(
                tenant_id=delivery.tenant_id,
                store_id=delivery.store_id,
                actor_identity_id=None,
                action=action,
                target_type="instagram_connection",
                target_public_id=connection.public_id,
                details_json=details,
            )
        )

    def ingest(
        self,
        *,
        raw_body: bytes,
        payload: dict[str, object],
        external_delivery_key: str | None,
        correlation_id: str | None,
    ) -> tuple[str, bool, int]:
        started = monotonic()
        payload_hash = canonical_payload_hash(raw_body)
        external_key = normalize_identifier(
            external_delivery_key,
            field="external delivery key",
            maximum=200,
        )
        delivery = InstagramWebhookDelivery(
            provider="meta",
            external_delivery_key=external_key,
            payload_hash=payload_hash,
            raw_payload=payload,
            signature_algorithm="sha256",
            signature_valid=True,
            verification_state="verified",
            processing_status="received",
            correlation_id=normalize_identifier(
                correlation_id, field="correlation ID", maximum=128
            ),
        )
        try:
            with self.session.begin_nested():
                self.session.add(delivery)
                self.session.flush()
        except IntegrityError:
            duplicate = self._find_duplicate(
                external_delivery_key=external_key,
                payload_hash=payload_hash,
            )
            if duplicate is None:
                self.session.rollback()
                raise
            duplicate.retry_count += 1
            self._audit_delivery(
                duplicate,
                action="instagram.webhook.duplicate",
                details={
                    "delivery_public_id": duplicate.public_id,
                    "correlation_id": correlation_id,
                },
            )
            self.session.commit()
            logger.info(
                "duplicate Instagram webhook",
                extra={"event_code": "instagram.webhook.duplicate"},
            )
            return "duplicate", True, 0

        try:
            parsed_events = parse_instagram_webhook(payload)
        except InstagramWebhookPayloadError:
            delivery.processing_status = "failed"
            delivery.failure_category = "invalid_payload"
            delivery.safe_failure_detail = "Webhook payload structure is invalid"
            delivery.processed_at = utc_now()
            self.session.commit()
            logger.warning(
                "Instagram webhook payload rejected",
                extra={"event_code": "instagram.webhook.invalid_payload"},
            )
            raise

        routing_ids = {
            item.routing_account_id
            for item in parsed_events
            if item.routing_account_id is not None
        }
        connections = list(
            self.session.scalars(
                select(InstagramConnection).where(
                    or_(
                        InstagramConnection.instagram_account_id.in_(routing_ids),
                        InstagramConnection.facebook_page_id.in_(routing_ids),
                    ),
                    InstagramConnection.status.in_(ROUTABLE_CONNECTION_STATUSES),
                )
            ).all()
        ) if routing_ids else []
        by_identifier: dict[str, InstagramConnection] = {}
        for connection in connections:
            by_identifier[connection.instagram_account_id] = connection
            if connection.facebook_page_id:
                by_identifier[connection.facebook_page_id] = connection
        resolved_connections = {
            by_identifier[item.routing_account_id].id
            for item in parsed_events
            if item.routing_account_id in by_identifier
        }
        if len(resolved_connections) != 1:
            delivery.processing_status = "ignored"
            delivery.failure_category = (
                "unknown_account"
                if not resolved_connections
                else "ambiguous_account_scope"
            )
            delivery.safe_failure_detail = (
                "No routable Instagram connection was resolved"
                if not resolved_connections
                else "Delivery spans multiple connection scopes"
            )
            delivery.processed_at = utc_now()
            self.session.commit()
            logger.info(
                "Instagram webhook ignored",
                extra={"event_code": "instagram.webhook.unresolved"},
            )
            return "ignored", False, 0

        connection_id = next(iter(resolved_connections))
        connection = next(item for item in connections if item.id == connection_id)
        delivery.tenant_id = connection.tenant_id
        delivery.store_id = connection.store_id
        delivery.instagram_connection_id = connection.id
        delivery.processing_status = "accepted"
        received_at = delivery.received_at
        created = 0
        duplicate_events = 0
        for parsed in parsed_events:
            if (
                parsed.routing_account_id not in by_identifier
                or by_identifier[parsed.routing_account_id].id != connection.id
            ):
                continue
            event = InstagramInboundEvent(
                tenant_id=connection.tenant_id,
                store_id=connection.store_id,
                instagram_connection_id=connection.id,
                webhook_delivery_id=delivery.id,
                provider="meta",
                provider_event_id=parsed.provider_event_id,
                idempotency_key=parsed.idempotency_key,
                event_type=parsed.event_type,
                object_type=parsed.object_type,
                external_object_id=parsed.external_object_id,
                external_sender_id=parsed.external_sender_id,
                external_recipient_id=parsed.external_recipient_id,
                provider_event_at=parsed.provider_event_at,
                normalized_payload=parsed.normalized_payload,
                processing_status=(
                    "ignored" if parsed.event_type == "unsupported" else "ready"
                ),
                occurred_at=parsed.provider_event_at or received_at,
                received_at=received_at,
            )
            try:
                with self.session.begin_nested():
                    self.session.add(event)
                    self.session.flush()
                created += 1
            except IntegrityError:
                existing = self.session.scalar(
                    select(InstagramInboundEvent.id).where(
                        InstagramInboundEvent.provider == "meta",
                        InstagramInboundEvent.idempotency_key
                        == parsed.idempotency_key,
                    )
                )
                if existing is None:
                    self.session.rollback()
                    raise
                duplicate_events += 1
        now = utc_now()
        # Operational receipt time intentionally does not participate in the
        # management revision. A Core update avoids turning a concurrent
        # webhook into a stale lifecycle write while preserving the timestamp.
        self.session.execute(
            update(InstagramConnection)
            .where(InstagramConnection.id == connection.id)
            .values(last_webhook_received_at=now, updated_at=now)
        )
        delivery.processing_status = "processed"
        delivery.processed_at = now
        self._audit_delivery(
            delivery,
            action="instagram.webhook.accepted",
            details={
                "delivery_public_id": delivery.public_id,
                "event_count": created,
                "duplicate_event_count": duplicate_events,
                "correlation_id": correlation_id,
            },
        )
        self.session.commit()
        logger.info(
            "Instagram webhook processed",
            extra={"event_code": "instagram.webhook.processed"},
        )
        _ = monotonic() - started
        return "accepted", False, created
