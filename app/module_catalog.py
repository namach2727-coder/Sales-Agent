from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import ModuleDefinition, Store, StoreInstagramConnection, StoreModule


@dataclass(frozen=True)
class ModuleSeed:
    code: str
    name: str
    description: str
    category: str
    monthly_price_irr: int
    availability: str = "ready"
    dependencies: tuple[str, ...] = ()
    default_limits: dict[str, int] = field(default_factory=dict)


# Prices are initial, provider-editable catalogue prices stored in IRR.
MODULE_SEEDS = (
    ModuleSeed(
        "sales_agent_core",
        "هسته دستیار فروش",
        "محصولات، کلمات مشابه، سؤال‌های پرتکرار و پاسخ‌گویی دایرکت",
        "sales",
        14_900_000,
        default_limits={"monthly_messages": 5000, "products": 200},
    ),
    ModuleSeed(
        "comments_to_dm",
        "کامنت به دایرکت",
        "تشخیص کامنت قیمت، ارسال پیام خصوصی و پاسخ عمومی زیر کامنت",
        "sales",
        5_900_000,
        dependencies=("sales_agent_core",),
        default_limits={"monthly_comments": 3000},
    ),
    ModuleSeed(
        "content_strategy",
        "استراتژی و تولید محتوا",
        "ساخت کپشن، هشتگ، فراخوان اقدام و عبارت فروش از داده محصول",
        "content",
        4_900_000,
        dependencies=("sales_agent_core",),
        default_limits={"monthly_drafts": 100},
    ),
    ModuleSeed(
        "content_review",
        "بازبینی و تأیید محتوا",
        "ویرایش، پیش‌نمایش و گردش تأیید مدیر پیش از انتشار",
        "content",
        2_900_000,
        default_limits={"reviewers": 3},
    ),
    ModuleSeed(
        "instagram_publish",
        "انتشار پست اینستاگرام",
        "انتشار کنترل‌شده عکس و متن تأییدشده در پیج حرفه‌ای",
        "content",
        3_900_000,
        availability="beta",
        dependencies=("content_review",),
        default_limits={"monthly_posts": 60},
    ),
    ModuleSeed(
        "order_confirmation",
        "ثبت و تأیید سفارش",
        "جمع‌آوری رنگ، سایز، تعداد و شماره تماس و ثبت سفارش برای اپراتور",
        "sales",
        3_900_000,
        dependencies=("sales_agent_core",),
        default_limits={"monthly_orders": 1000},
    ),
    ModuleSeed(
        "operator_handoff",
        "تحویل به اپراتور",
        "تشخیص مکالمه حساس و تحویل سریع مشتری به نیروی انسانی",
        "sales",
        2_900_000,
        dependencies=("sales_agent_core",),
    ),
    ModuleSeed(
        "receipt_review",
        "بررسی فیش پرداخت",
        "دریافت فیش و آماده‌سازی آن برای کنترل مبلغ، شماره پیگیری و تأیید مدیر",
        "operations",
        6_900_000,
        availability="beta",
        dependencies=("order_confirmation",),
        default_limits={"monthly_receipts": 500},
    ),
    ModuleSeed(
        "analytics",
        "گزارش و تحلیل فروش",
        "داشبورد سرنخ، سفارش، نرخ پاسخ و عملکرد کامنت و محتوا",
        "analytics",
        4_900_000,
        availability="planned",
        dependencies=("sales_agent_core",),
    ),
)

DEFAULT_ACTIVE_MODULES = {
    "sales_agent_core",
    "comments_to_dm",
    "content_strategy",
    "content_review",
    "order_confirmation",
    "operator_handoff",
}

# New commercial tenants receive no billable capability implicitly. The
# provider must request modules explicitly; dependency expansion is handled by
# the provisioning workflow. Legacy demo-store activation remains separate.
DEFAULT_PROVISIONING_MODULES: frozenset[str] = frozenset()


def seed_module_catalog(db: Session) -> None:
    existing = {
        item.code: item
        for item in db.scalars(select(ModuleDefinition)).all()
    }
    for index, seed in enumerate(MODULE_SEEDS):
        if seed.code in existing:
            continue
        db.add(
            ModuleDefinition(
                code=seed.code,
                name=seed.name,
                short_description=seed.description,
                category=seed.category,
                monthly_price=seed.monthly_price_irr,
                setup_price=0,
                currency="IRR",
                dependencies=list(seed.dependencies),
                default_limits=dict(seed.default_limits),
                availability=seed.availability,
                is_sellable=True,
                sort_order=index,
            )
        )
    db.flush()


def ensure_store_modules(
    db: Session,
    store: Store,
    *,
    activate_legacy_defaults: bool = False,
) -> None:
    seed_module_catalog(db)
    existing_codes = set(
        db.scalars(
            select(StoreModule.module_code).where(StoreModule.store_id == store.id)
        ).all()
    )
    definitions = db.scalars(select(ModuleDefinition)).all()
    for definition in definitions:
        if definition.code in existing_codes:
            continue
        db.add(
            StoreModule(
                store_id=store.id,
                module_code=definition.code,
                status=(
                    "active"
                    if activate_legacy_defaults and definition.code in DEFAULT_ACTIVE_MODULES
                    else "inactive"
                ),
                currency=definition.currency,
                billing_interval="month",
                limits_json=dict(definition.default_limits or {}),
                source="legacy" if activate_legacy_defaults else "manual",
            )
        )
    db.flush()


def _time_valid(entitlement: StoreModule, now: datetime) -> bool:
    def comparable(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    starts_at = comparable(entitlement.starts_at)
    ends_at = comparable(entitlement.ends_at)
    trial_ends_at = comparable(entitlement.trial_ends_at)
    current_period_end = comparable(entitlement.current_period_end)
    if starts_at and starts_at > now:
        return False
    if ends_at and ends_at <= now:
        return False
    if entitlement.status == "trial" and trial_ends_at:
        return trial_ends_at > now
    if entitlement.status == "active" and current_period_end:
        return current_period_end > now
    return True


def module_enabled(
    db: Session,
    store: Store,
    code: str,
    *,
    now: datetime | None = None,
    _seen: set[str] | None = None,
) -> bool:
    if store.status in {"suspended", "disabled", "deleted"}:
        return False
    entitlement = db.scalar(
        select(StoreModule)
        .options(joinedload(StoreModule.module))
        .where(
            StoreModule.store_id == store.id,
            StoreModule.module_code == code,
        )
    )
    if entitlement is None or entitlement.status not in {"active", "trial"}:
        return False
    if entitlement.module.availability == "planned":
        return False
    current = now or datetime.now(UTC)
    if not _time_valid(entitlement, current):
        return False
    seen = set(_seen or ())
    if code in seen:
        return False
    seen.add(code)
    for dependency in entitlement.module.dependencies or []:
        if not module_enabled(db, store, str(dependency), now=current, _seen=seen):
            return False
    return True


def effective_price_irr(entitlement: StoreModule) -> int:
    if entitlement.custom_monthly_price is not None:
        return entitlement.custom_monthly_price
    return entitlement.module.monthly_price


def store_subdomain(store: Store, settings: Settings) -> tuple[str, str]:
    base = settings.tenant_base_domain.strip().lower().strip(".")
    if base:
        host = f"{store.slug}.{base}"
        return host, f"{settings.tenant_url_scheme}://{host}/admin"
    host = f"{store.slug}.localhost:8000"
    return host, f"http://{host}/admin"


def store_for_instagram_account(
    db: Session,
    ig_user_id: str,
    settings: Settings,
) -> Store | None:
    connection = db.scalar(
        select(StoreInstagramConnection)
        .options(joinedload(StoreInstagramConnection.store))
        .where(
            StoreInstagramConnection.ig_user_id == ig_user_id,
            StoreInstagramConnection.status == "active",
        )
    )
    if connection is not None:
        return connection.store
    if settings.meta_ig_user_id.strip() == ig_user_id:
        return db.scalar(select(Store).where(Store.slug == "default"))
    return None


def ensure_default_instagram_connection(
    db: Session,
    store: Store,
    settings: Settings,
) -> None:
    ig_user_id = settings.meta_ig_user_id.strip()
    if not ig_user_id or ig_user_id.lower() == "replace-me":
        return
    existing_for_store = db.scalar(
        select(StoreInstagramConnection).where(
            StoreInstagramConnection.store_id == store.id
        )
    )
    existing_for_account = db.scalar(
        select(StoreInstagramConnection).where(
            StoreInstagramConnection.ig_user_id == ig_user_id
        )
    )
    if existing_for_store is not None:
        # Development and tests may rotate the configured account. Updating the
        # one connection owned by the legacy store is both idempotent and avoids
        # violating the one-connection-per-store constraint.
        if (
            existing_for_account is None
            or existing_for_account.id == existing_for_store.id
        ):
            existing_for_store.ig_user_id = ig_user_id
            existing_for_store.status = "active"
        return
    if existing_for_account is None:
        db.add(
            StoreInstagramConnection(
                store_id=store.id,
                ig_user_id=ig_user_id,
                status="active",
            )
        )


def serialize_store_marketplace(
    db: Session,
    store: Store,
    settings: Settings,
    *,
    can_manage_modules: bool,
) -> dict[str, object]:
    db.flush()
    entitlements = list(
        db.scalars(
            select(StoreModule)
            .options(joinedload(StoreModule.module))
            .where(StoreModule.store_id == store.id)
            .order_by(StoreModule.id)
        ).all()
    )
    entitlements.sort(key=lambda item: (item.module.sort_order, item.module.code))
    host, url = store_subdomain(store, settings)
    modules: list[dict[str, object]] = []
    monthly_total = 0
    for item in entitlements:
        enabled = module_enabled(db, store, item.module_code)
        price = effective_price_irr(item)
        if enabled:
            monthly_total += price
        modules.append(
            {
                "code": item.module_code,
                "name": item.module.name,
                "description": item.module.short_description,
                "category": item.module.category,
                "availability": item.module.availability,
                "status": item.status,
                "enabled": enabled,
                "monthly_price_irr": price,
                "catalog_price_irr": item.module.monthly_price,
                "setup_price_irr": item.module.setup_price,
                "currency": item.currency,
                "dependencies": list(item.module.dependencies or []),
                "limits": dict(item.limits_json or {}),
                "trial_ends_at": (
                    item.trial_ends_at.isoformat() if item.trial_ends_at else None
                ),
            }
        )
    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "slug": store.slug,
            "subdomain": host,
            "url": url,
            "status": store.status,
        },
        "can_manage_modules": can_manage_modules,
        "monthly_total_irr": monthly_total,
        "modules": modules,
    }
