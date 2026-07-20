"""Deterministically ordered provisioning step contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.provisioning.context import TenantProvisioningContext


@dataclass(frozen=True, slots=True)
class TenantProvisioningStep:
    name: str
    order: int
    handler: Callable[[TenantProvisioningContext], None]
