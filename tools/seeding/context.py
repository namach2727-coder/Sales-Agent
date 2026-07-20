"""Typed seed execution context, outcomes, and safe reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.tenancy import TenantContext


class SeedProfile(str, Enum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TEST = "test"
    DEMO = "demo"

    @classmethod
    def parse(cls, value: str | "SeedProfile") -> "SeedProfile":
        if isinstance(value, cls):
            return value
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            allowed = ", ".join(profile.value for profile in cls)
            raise SeedValidationError(
                f"unknown seed profile {value!r}; choose one of: {allowed}"
            ) from exc


class SeedScope(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant"


class SeedOwnership(str, Enum):
    CREATE_ONLY = "create_only"
    UPSERT_SEED_OWNED = "upsert_seed_owned"
    VERIFY_ONLY = "verify_only"


class SeedStatus(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"
    FAILED = "failed"


class SeedError(RuntimeError):
    """Base error for safe, explicit seed operations."""


class SeedValidationError(SeedError):
    """Raised before writes when a seed request violates policy."""


@dataclass(frozen=True, slots=True)
class SeedContext:
    session: Session
    profile: SeedProfile
    tenant: TenantContext | None
    dry_run: bool

    @property
    def tenant_id(self) -> int:
        if self.tenant is None:
            raise SeedValidationError("tenant-scoped seed requires an explicit tenant")
        return self.tenant.store_id


@dataclass(frozen=True, slots=True)
class SeedMutation:
    status: SeedStatus
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    summary: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if any(value < 0 for value in (self.created, self.updated, self.unchanged, self.skipped)):
            raise ValueError("seed mutation counters cannot be negative")


@dataclass(frozen=True, slots=True)
class SeedResult:
    seed_name: str
    seed_version: str
    status: SeedStatus
    scope: SeedScope
    tenant_slug: str | None
    dry_run: bool
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0
    summary: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SeedReport:
    profile: SeedProfile
    dry_run: bool
    results: tuple[SeedResult, ...]

    @property
    def counts(self) -> dict[str, int]:
        counts = {status.value: 0 for status in SeedStatus}
        for result in self.results:
            counts[result.status.value] += 1
        return counts


class SeedExecutionError(SeedError):
    """Raised after rolling back a failed seed transaction."""

    def __init__(
        self,
        seed_name: str,
        result: SeedResult,
        report: SeedReport | None = None,
    ):
        super().__init__(f"seed {seed_name!r} failed and was rolled back")
        self.seed_name = seed_name
        self.result = result
        self.report = report
