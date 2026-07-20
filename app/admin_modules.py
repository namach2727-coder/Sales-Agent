from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.admin import require_admin_mutation, require_admin_read
from app.admin_schemas import (
    ModulePriceUpdateInput,
    StoreCreateInput,
    StoreModuleUpdateInput,
)
from app.catalog_training import ensure_default_store
from app.config import Settings, get_settings
from app.database import get_db
from app.models import AdminAuditLog, ModuleDefinition, Store, StoreModule
from app.module_catalog import (
    ensure_store_modules,
    module_enabled,
    seed_module_catalog,
    serialize_store_marketplace,
    store_subdomain,
)
from app.tenancy import normalize_store_slug, store_by_slug


router = APIRouter(tags=["admin-module-marketplace"])


def _ensure_catalog_and_legacy_store(db: Session) -> Store:
    store = ensure_default_store(db)
    seed_module_catalog(db)
    ensure_store_modules(db, store, activate_legacy_defaults=True)
    db.commit()
    return store


@router.get(
    "/admin/api/module-marketplace",
    dependencies=[Depends(require_admin_read)],
)
def module_marketplace(
    store_slug: str = Query(default="default", min_length=1, max_length=63),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _ensure_catalog_and_legacy_store(db)
    try:
        slug = normalize_store_slug(store_slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store = store_by_slug(db, slug)
    ensure_store_modules(db, store)
    db.commit()
    return serialize_store_marketplace(
        db, store, settings, can_manage_modules=True
    )


@router.get(
    "/admin/api/provider/stores",
    dependencies=[Depends(require_admin_read)],
)
def provider_stores(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _ensure_catalog_and_legacy_store(db)
    stores = list(db.scalars(select(Store).order_by(Store.id)).all())
    return {
        "stores": [
            {
                "id": store.id,
                "name": store.name,
                "slug": store.slug,
                "status": store.status,
                "subdomain": store_subdomain(store, settings)[0],
                "url": store_subdomain(store, settings)[1],
            }
            for store in stores
            if store.status != "deleted"
        ]
    }


@router.post(
    "/admin/api/provider/stores",
    dependencies=[Depends(require_admin_mutation)],
)
def create_provider_store(
    payload: StoreCreateInput,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _ensure_catalog_and_legacy_store(db)
    try:
        slug = normalize_store_slug(payload.slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store = Store(name=payload.name.strip(), slug=slug, status="onboarding")
    db.add(store)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="این ساب‌دامنه قبلاً استفاده شده است."
        ) from exc
    ensure_store_modules(db, store, activate_legacy_defaults=False)
    db.add(
        AdminAuditLog(
            store_id=store.id,
            action="store_created",
            entity_type="store",
            entity_id=str(store.id),
            details_json={"slug": store.slug},
        )
    )
    db.commit()
    return serialize_store_marketplace(
        db, store, settings, can_manage_modules=True
    )


def _dependency_names(
    db: Session, store: Store, definition: ModuleDefinition
) -> list[str]:
    dependencies = list(definition.dependencies or [])
    if not dependencies:
        return []
    rows = list(
        db.scalars(
            select(StoreModule)
            .options(joinedload(StoreModule.module))
            .where(
                StoreModule.store_id == store.id,
                StoreModule.module_code.in_(dependencies),
            )
        ).all()
    )
    active_codes = {
        row.module_code
        for row in rows
        if module_enabled(db, store, row.module_code)
    }
    return [
        row.module.name
        for row in rows
        if row.module_code not in active_codes
    ] + [code for code in dependencies if code not in {row.module_code for row in rows}]


@router.patch(
    "/admin/api/provider/stores/{store_slug}/modules/{module_code}",
    dependencies=[Depends(require_admin_mutation)],
)
def update_store_module(
    store_slug: str,
    module_code: str,
    payload: StoreModuleUpdateInput,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _ensure_catalog_and_legacy_store(db)
    try:
        normalized_slug = normalize_store_slug(store_slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    store = store_by_slug(db, normalized_slug)
    ensure_store_modules(db, store)
    entitlement = db.scalar(
        select(StoreModule)
        .options(joinedload(StoreModule.module))
        .where(
            StoreModule.store_id == store.id,
            StoreModule.module_code == module_code,
        )
    )
    if entitlement is None:
        raise HTTPException(status_code=404, detail="ماژول پیدا نشد.")
    if entitlement.module.availability == "planned" and payload.status in {
        "active",
        "trial",
    }:
        raise HTTPException(
            status_code=409,
            detail="این ماژول هنوز در برنامه توسعه است و قابل فعال‌سازی نیست.",
        )
    if payload.status in {"active", "trial"}:
        missing = _dependency_names(db, store, entitlement.module)
        if missing:
            raise HTTPException(
                status_code=409,
                detail=f"ابتدا ماژول‌های وابسته را فعال کنید: {', '.join(missing)}",
            )
    entitlement.status = payload.status
    entitlement.custom_monthly_price = payload.custom_monthly_price_irr
    entitlement.starts_at = entitlement.starts_at or datetime.now(UTC)
    if payload.status == "trial":
        entitlement.trial_ends_at = datetime.now(UTC) + timedelta(
            days=payload.trial_days or 7
        )
    elif payload.status != "trial":
        entitlement.trial_ends_at = None
    db.add(
        AdminAuditLog(
            store_id=store.id,
            action="module_status_updated",
            entity_type="store_module",
            entity_id=module_code,
            details_json={"status": payload.status},
        )
    )
    db.commit()
    return serialize_store_marketplace(
        db, store, settings, can_manage_modules=True
    )


@router.patch(
    "/admin/api/provider/module-catalog/{module_code}",
    dependencies=[Depends(require_admin_mutation)],
)
def update_catalog_price(
    module_code: str,
    payload: ModulePriceUpdateInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _ensure_catalog_and_legacy_store(db)
    definition = db.get(ModuleDefinition, module_code)
    if definition is None:
        raise HTTPException(status_code=404, detail="ماژول پیدا نشد.")
    definition.monthly_price = payload.monthly_price_irr
    definition.setup_price = payload.setup_price_irr
    db.commit()
    return {
        "code": definition.code,
        "monthly_price_irr": definition.monthly_price,
        "setup_price_irr": definition.setup_price,
        "currency": definition.currency,
    }
