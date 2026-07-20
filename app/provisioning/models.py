"""Typed provisioning requests and credential-free results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProvisioningStatus(str, Enum):
    PLANNED = "planned"
    SUCCEEDED = "succeeded"


@dataclass(frozen=True, slots=True)
class TenantProvisioningRequest:
    name: str
    slug: str
    profile: str
    requested_module_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TenantProvisioningResult:
    operation_id: str
    tenant_id: int
    tenant_name: str
    tenant_slug: str
    tenant_status: str
    profile: str
    status: ProvisioningStatus
    completed_steps: tuple[str, ...]
    seed_names: tuple[str, ...]
    module_codes: tuple[str, ...]
    dry_run: bool
