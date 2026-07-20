"""Seed definitions, duplicate protection, and dependency ordering."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re

from tools.seeding.context import (
    SeedContext,
    SeedMutation,
    SeedOwnership,
    SeedProfile,
    SeedScope,
    SeedValidationError,
)


SEED_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$")


@dataclass(frozen=True, slots=True)
class SeedDefinition:
    name: str
    version: str
    scope: SeedScope
    compatible_profiles: frozenset[SeedProfile]
    production_safe: bool
    ownership: SeedOwnership
    handler: Callable[[SeedContext], SeedMutation]
    order: int = 100
    dependencies: tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if SEED_NAME_PATTERN.fullmatch(self.name) is None:
            raise ValueError(
                "seed name must be a dotted lowercase identifier, for example system.modules"
            )
        if not self.version.strip():
            raise ValueError("seed version is required")
        if not self.compatible_profiles:
            raise ValueError("seed must explicitly declare compatible profiles")


class SeedRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, SeedDefinition] = {}

    def register(self, definition: SeedDefinition) -> None:
        if definition.name in self._definitions:
            raise SeedValidationError(f"duplicate seed name {definition.name!r}")
        self._definitions[definition.name] = definition

    def definitions(self) -> tuple[SeedDefinition, ...]:
        return tuple(sorted(self._definitions.values(), key=lambda item: (item.order, item.name)))

    def select(
        self,
        profile: SeedProfile,
        *,
        names: Iterable[str] | None = None,
        tenant_supplied: bool,
    ) -> tuple[SeedDefinition, ...]:
        requested = tuple(dict.fromkeys(names or ()))
        if requested:
            missing = sorted(name for name in requested if name not in self._definitions)
            if missing:
                raise SeedValidationError(f"unknown seed name(s): {', '.join(missing)}")
            selected_names = set(requested)
            for name in requested:
                self._include_dependencies(name, selected_names, stack=())
        else:
            selected_names = {
                item.name
                for item in self._definitions.values()
                if profile in item.compatible_profiles
                and (tenant_supplied or item.scope is SeedScope.GLOBAL)
            }

        selected = [self._definitions[name] for name in selected_names]
        for definition in selected:
            if profile not in definition.compatible_profiles:
                raise SeedValidationError(
                    f"seed {definition.name!r} is not compatible with profile {profile.value!r}"
                )
            if profile is SeedProfile.PRODUCTION and not definition.production_safe:
                raise SeedValidationError(
                    f"production profile rejects non-production-safe seed {definition.name!r}"
                )
            if definition.scope is SeedScope.TENANT and not tenant_supplied:
                raise SeedValidationError(
                    f"tenant-scoped seed {definition.name!r} requires --tenant"
                )
        return self._ordered(selected)

    def _include_dependencies(
        self,
        name: str,
        selected: set[str],
        *,
        stack: tuple[str, ...],
    ) -> None:
        if name in stack:
            cycle = " -> ".join((*stack, name))
            raise SeedValidationError(f"seed dependency cycle: {cycle}")
        definition = self._definitions[name]
        for dependency in definition.dependencies:
            if dependency not in self._definitions:
                raise SeedValidationError(
                    f"seed {name!r} depends on unknown seed {dependency!r}"
                )
            selected.add(dependency)
            self._include_dependencies(
                dependency, selected, stack=(*stack, name)
            )

    def _ordered(self, definitions: list[SeedDefinition]) -> tuple[SeedDefinition, ...]:
        available = {definition.name: definition for definition in definitions}
        ordered: list[SeedDefinition] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(definition: SeedDefinition) -> None:
            if definition.name in visited:
                return
            if definition.name in visiting:
                raise SeedValidationError(
                    f"seed dependency cycle includes {definition.name!r}"
                )
            visiting.add(definition.name)
            for dependency_name in definition.dependencies:
                dependency = available.get(dependency_name)
                if dependency is None:
                    raise SeedValidationError(
                        f"selected seed {definition.name!r} requires {dependency_name!r}"
                    )
                visit(dependency)
            visiting.remove(definition.name)
            visited.add(definition.name)
            ordered.append(definition)

        for definition in sorted(definitions, key=lambda item: (item.order, item.name)):
            visit(definition)
        return tuple(ordered)

