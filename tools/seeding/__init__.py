"""Explicit seed framework public API."""

from tools.seeding.context import (
    SeedContext,
    SeedError,
    SeedExecutionError,
    SeedMutation,
    SeedOwnership,
    SeedProfile,
    SeedReport,
    SeedResult,
    SeedScope,
    SeedStatus,
    SeedValidationError,
)
from tools.seeding.registry import SeedDefinition, SeedRegistry
from tools.seeding.runner import SeedRunner
from tools.seeding.seeds.system import register_system_seeds
from tools.seeding.seeds.authorization import register_authorization_seeds


def default_registry() -> SeedRegistry:
    registry = SeedRegistry()
    register_system_seeds(registry)
    register_authorization_seeds(registry)
    return registry


__all__ = [
    "SeedContext",
    "SeedDefinition",
    "SeedError",
    "SeedExecutionError",
    "SeedMutation",
    "SeedOwnership",
    "SeedProfile",
    "SeedRegistry",
    "SeedReport",
    "SeedResult",
    "SeedRunner",
    "SeedScope",
    "SeedStatus",
    "SeedValidationError",
    "default_registry",
]
