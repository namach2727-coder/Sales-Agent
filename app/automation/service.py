"""Persisted store automation policy and its audit trail."""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Store, TenantAuditLog, utc_now


class AutomationControlError(Exception):
    code = "automation_control_error"


class AutomationControlConflict(AutomationControlError):
    code = "stale_revision"


class AutomationControlService:
    def __init__(
        self,
        session: Session,
        *,
        tenant_id: int,
        store_id: int,
        actor_identity_id: int | None = None,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.store_id = store_id
        self.actor_identity_id = actor_identity_id

    def read(self) -> Store:
        store = self.session.get(Store, self.store_id)
        if store is None or store.tenant_id != self.tenant_id:
            raise AutomationControlError("store not found")
        return store

    def update(self, *, enabled: bool, expected_revision: int) -> Store:
        store = self.read()
        if store.automation_revision != expected_revision:
            raise AutomationControlConflict("automation revision does not match")
        changed_at = utc_now()
        result = self.session.execute(
            update(Store)
            .where(
                Store.id == self.store_id,
                Store.tenant_id == self.tenant_id,
                Store.automation_revision == expected_revision,
            )
            .values(
                automation_enabled=enabled,
                automation_revision=expected_revision + 1,
                updated_at=changed_at,
            )
        )
        if result.rowcount != 1:
            self.session.rollback()
            raise AutomationControlConflict("automation revision does not match")
        self.session.add(
            TenantAuditLog(
                tenant_id=self.tenant_id,
                store_id=self.store_id,
                actor_identity_id=self.actor_identity_id,
                action=(
                    "store.automation_enabled"
                    if enabled
                    else "store.automation_disabled"
                ),
                target_type="store",
                target_public_id=store.public_id,
                details_json={
                    "enabled": enabled,
                    "previous_revision": expected_revision,
                    "revision": expected_revision + 1,
                },
            )
        )
        self.session.commit()
        self.session.expire(store)
        return self.read()


def automation_is_enabled(
    session: Session,
    *,
    tenant_id: int,
    store_id: int,
) -> bool:
    """Read the server-authoritative switch at the shared AI boundary."""

    store = session.get(Store, store_id)
    return bool(
        store is not None
        and store.tenant_id == tenant_id
        and store.automation_enabled
    )
