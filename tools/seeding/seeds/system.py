"""Minimal system catalog and tenant entitlement seeds."""

from __future__ import annotations

from sqlalchemy import select

from app.models import ModuleDefinition, SaasPlan, StoreModule
from app.module_catalog import MODULE_SEEDS
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


def seed_module_definitions(context: SeedContext) -> SeedMutation:
    existing = {
        item.code: item
        for item in context.session.scalars(select(ModuleDefinition)).all()
    }
    created = 0
    for index, item in enumerate(MODULE_SEEDS):
        if item.code in existing:
            continue
        context.session.add(
            ModuleDefinition(
                code=item.code,
                name=item.name,
                short_description=item.description,
                category=item.category,
                monthly_price=item.monthly_price_irr,
                setup_price=0,
                currency="IRR",
                dependencies=list(item.dependencies),
                default_limits=dict(item.default_limits),
                availability=item.availability,
                is_sellable=True,
                sort_order=index,
            )
        )
        created += 1
    unchanged = len(MODULE_SEEDS) - created
    return SeedMutation(
        status=SeedStatus.CREATED if created else SeedStatus.UNCHANGED,
        created=created,
        unchanged=unchanged,
        summary={"catalog": "module_definitions"},
    )


def seed_saas_plans(context: SeedContext) -> SeedMutation:
    """Reconcile the provider-owned, backend-authoritative MVP plan catalog."""

    definitions = (
        {
            "code": "FREE",
            "name": "Forever Free",
            "price_amount": 0,
            "reply_limit": 20,
            "automation_limit": 1,
            "instagram_account_limit": 1,
            "duration_days": None,
            "module_codes": ["sales_agent_core"],
            "is_active": False,
        },
        {
            "code": "TRIAL",
            "name": "Trial",
            "price_amount": 0,
            "reply_limit": 200,
            "automation_limit": 3,
            "instagram_account_limit": 1,
            "duration_days": 14,
            "module_codes": ["sales_agent_core"],
            "is_active": True,
        },
        {
            "code": "START",
            "name": "Start",
            "price_amount": 2_990_000,
            "reply_limit": 1_500,
            "automation_limit": 10,
            "instagram_account_limit": 1,
            "duration_days": 30,
            "module_codes": ["sales_agent_core"],
            "is_active": True,
        },
        {
            "code": "PRO",
            "name": "Pro",
            "price_amount": 6_990_000,
            "reply_limit": 5_000,
            "automation_limit": 30,
            "instagram_account_limit": 1,
            "duration_days": 30,
            "module_codes": ["sales_agent_core"],
            "is_active": True,
        },
    )
    existing = {
        item.code: item for item in context.session.scalars(select(SaasPlan)).all()
    }
    created = 0
    updated = 0
    unchanged = 0
    for item in definitions:
        plan = existing.get(item["code"])
        if plan is None:
            context.session.add(SaasPlan(currency="IRR", **item))
            created += 1
            continue
        desired = {"currency": "IRR", **item}
        changed = False
        for field, value in desired.items():
            if getattr(plan, field) != value:
                setattr(plan, field, value)
                changed = True
        updated += int(changed)
        unchanged += int(not changed)

    # Retain legacy rows for referential integrity, but never advertise them.
    for legacy_code in ("PILOT",):
        legacy = existing.get(legacy_code)
        if legacy is not None and legacy.is_active:
            legacy.is_active = False
            updated += 1

    status = (
        SeedStatus.CREATED
        if created
        else SeedStatus.UPDATED
        if updated
        else SeedStatus.UNCHANGED
    )
    return SeedMutation(
        status=status,
        created=created,
        updated=updated,
        unchanged=unchanged,
        summary={"catalog": "saas_plans"},
    )


def seed_tenant_module_entitlements(context: SeedContext) -> SeedMutation:
    tenant_id = context.tenant_id
    existing_codes = set(
        context.session.scalars(
            select(StoreModule.module_code).where(StoreModule.store_id == tenant_id)
        ).all()
    )
    definitions = list(
        context.session.scalars(
            select(ModuleDefinition).order_by(ModuleDefinition.sort_order, ModuleDefinition.code)
        ).all()
    )
    created = 0
    for definition in definitions:
        if definition.code in existing_codes:
            continue
        context.session.add(
            StoreModule(
                store_id=tenant_id,
                module_code=definition.code,
                status="inactive",
                currency=definition.currency,
                billing_interval="month",
                limits_json=dict(definition.default_limits or {}),
                source="seed",
            )
        )
        created += 1
    unchanged = len(definitions) - created
    return SeedMutation(
        status=SeedStatus.CREATED if created else SeedStatus.UNCHANGED,
        created=created,
        unchanged=unchanged,
        summary={"catalog": "tenant_module_entitlements"},
    )


def register_system_seeds(registry: SeedRegistry) -> None:
    registry.register(
        SeedDefinition(
            name="system.module_definitions",
            version="1",
            scope=SeedScope.GLOBAL,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_module_definitions,
            order=10,
            description="Create missing provider module definitions without overwriting edits.",
        )
    )
    registry.register(
        SeedDefinition(
            name="system.saas_plans",
            version="2",
            scope=SeedScope.GLOBAL,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.UPSERT_SEED_OWNED,
            handler=seed_saas_plans,
            dependencies=("system.module_definitions",),
            order=15,
            description="Reconcile the provider-owned MVP Trial, Start, and Pro plan catalog.",
        )
    )
    registry.register(
        SeedDefinition(
            name="tenant.module_entitlements",
            version="1",
            scope=SeedScope.TENANT,
            compatible_profiles=ALL_PROFILES,
            production_safe=True,
            ownership=SeedOwnership.CREATE_ONLY,
            handler=seed_tenant_module_entitlements,
            dependencies=("system.module_definitions",),
            order=20,
            description="Create missing inactive module entitlements for one explicit tenant.",
        )
    )

