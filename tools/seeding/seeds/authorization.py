"""Production-safe authorization catalog seeds."""

from __future__ import annotations

from sqlalchemy import select

from app.authz.permissions import PERMISSION_DEFINITIONS, ROLE_DEFINITIONS
from app.models import AuthPermission, AuthRole, AuthRolePermission
from tools.seeding.context import (
    SeedContext,
    SeedMutation,
    SeedOwnership,
    SeedProfile,
    SeedScope,
    SeedStatus,
)
from tools.seeding.registry import SeedDefinition, SeedRegistry


ALL_PROFILES = frozenset(SeedProfile)


def seed_auth_permissions(context: SeedContext) -> SeedMutation:
    existing = set(context.session.scalars(select(AuthPermission.code)).all())
    created = 0
    for item in PERMISSION_DEFINITIONS:
        if item.code in existing:
            continue
        context.session.add(
            AuthPermission(
                code=item.code,
                scope=item.scope.value,
                description=item.description,
                system_managed=True,
            )
        )
        created += 1
    return SeedMutation(
        status=SeedStatus.CREATED if created else SeedStatus.UNCHANGED,
        created=created,
        unchanged=len(PERMISSION_DEFINITIONS) - created,
        summary={"catalog": "auth_permissions"},
    )


def seed_auth_roles(context: SeedContext) -> SeedMutation:
    existing = set(context.session.scalars(select(AuthRole.code)).all())
    created = 0
    for item in ROLE_DEFINITIONS:
        if item.code in existing:
            continue
        context.session.add(
            AuthRole(
                code=item.code,
                display_name=item.display_name,
                scope=item.scope.value,
                description=item.description,
                system_managed=True,
            )
        )
        created += 1
    return SeedMutation(
        status=SeedStatus.CREATED if created else SeedStatus.UNCHANGED,
        created=created,
        unchanged=len(ROLE_DEFINITIONS) - created,
        summary={"catalog": "auth_roles"},
    )


def seed_auth_role_permissions(context: SeedContext) -> SeedMutation:
    existing = set(
        context.session.execute(
            select(AuthRolePermission.role_code, AuthRolePermission.permission_code)
        ).all()
    )
    expected = {
        (role.code, permission_code)
        for role in ROLE_DEFINITIONS
        for permission_code in role.permission_codes
    }
    created = 0
    for role_code, permission_code in sorted(expected):
        if (role_code, permission_code) in existing:
            continue
        context.session.add(
            AuthRolePermission(
                role_code=role_code,
                permission_code=permission_code,
            )
        )
        created += 1
    return SeedMutation(
        status=SeedStatus.CREATED if created else SeedStatus.UNCHANGED,
        created=created,
        unchanged=len(expected) - created,
        summary={"catalog": "auth_role_permissions"},
    )


def register_authorization_seeds(registry: SeedRegistry) -> None:
    registry.register(
        SeedDefinition(
            name="system.auth_permissions",
            version="2",
            scope=SeedScope.GLOBAL,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_auth_permissions,
            order=30,
            description="Create stable authorization permission definitions.",
        )
    )
    registry.register(
        SeedDefinition(
            name="system.auth_roles",
            version="2",
            scope=SeedScope.GLOBAL,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_auth_roles,
            order=40,
            description="Create system-managed platform and tenant roles.",
        )
    )
    registry.register(
        SeedDefinition(
            name="system.auth_role_permissions",
            version="2",
            scope=SeedScope.GLOBAL,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_auth_role_permissions,
            order=50,
            dependencies=("system.auth_permissions", "system.auth_roles"),
            description="Create explicit role-to-permission mappings.",
        )
    )
