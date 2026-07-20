"""Mutable state scoped to one provisioning operation."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Store
from app.provisioning.models import TenantProvisioningRequest
from app.tenancy import TenantContext
from tools.seeding import SeedProfile, SeedResult


@dataclass(slots=True)
class TenantProvisioningContext:
    session: Session
    request: TenantProvisioningRequest
    profile: SeedProfile
    operation_id: str
    dry_run: bool
    tenant: Store | None = None
    tenant_context: TenantContext | None = None
    selected_module_codes: tuple[str, ...] = ()
    seed_results: list[SeedResult] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
