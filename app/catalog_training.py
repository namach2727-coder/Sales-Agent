import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.catalog_text import normalize_catalog_text
from app.models import (
    AdminAuditLog,
    CatalogProduct,
    FAQ,
    KnowledgeItem,
    KnowledgeVersion,
    Product,
    ProductAlias,
    ProductCategory,
    Store,
    TrainingDraft,
)


DEFAULT_STORE_SLUG = "default"

CATEGORY_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("قاب", "کاور", "cover", "case"), "لوازم جانبی / قاب موبایل"),
    (("آیفون", "ایفون", "iphone", "apple"), "موبایل / اپل"),
    (("سامسونگ", "samsung", "galaxy"), "موبایل / سامسونگ"),
    (("شیائومی", "xiaomi", "redmi", "poco"), "موبایل / شیائومی"),
    (("موبایل", "گوشی", "android"), "موبایل"),
    (("لباس", "پیراهن", "شلوار", "مانتو"), "پوشاک"),
    (("کفش", "کتانی", "صندل"), "کفش"),
    (("کرم", "آرایشی", "پوست", "مو"), "آرایشی و بهداشتی"),
)

STOP_WORDS = {
    "آیا",
    "است",
    "چیست",
    "چطور",
    "چگونه",
    "برای",
    "دارد",
    "دارید",
    "شود",
    "می",
    "های",
}


class CatalogPublishError(ValueError):
    pass


def ensure_default_store(db: Session, name: str = "فروشگاه آزمایشی") -> Store:
    store = db.scalar(select(Store).where(Store.slug == DEFAULT_STORE_SLUG))
    if store is None:
        store = Store(name=name, slug=DEFAULT_STORE_SLUG, status="onboarding")
        db.add(store)
        db.flush()
    return store


def infer_category(name: str, description: str | None, keywords: list[str]) -> str:
    haystack = normalize_catalog_text(
        " ".join([name, description or "", *keywords])
    )
    for triggers, category in CATEGORY_RULES:
        if any(normalize_catalog_text(trigger) in haystack for trigger in triggers):
            return category
    return "سایر محصولات"


def _alias(
    value: str,
    kind: str,
    source: str,
    priority: int,
) -> dict[str, object] | None:
    cleaned = value.strip()
    normalized = normalize_catalog_text(cleaned)
    if not normalized or len(cleaned) > 200:
        return None
    return {
        "value": cleaned,
        "normalized_value": normalized,
        "kind": kind,
        "source": source,
        "priority": priority,
        "approved": True,
    }


def _generated_product_aliases(name: str) -> list[str]:
    normalized = normalize_catalog_text(name)
    generated: list[str] = []

    without_storage = re.sub(
        r"(?<!\w)\d+\s*(?:gb|tb|گیگ(?:ابایت)?|ترابایت)(?!\w)",
        " ",
        normalized,
        flags=re.IGNORECASE,
    )
    without_storage = re.sub(r"\s+", " ", without_storage).strip()
    if without_storage and without_storage != normalized:
        generated.append(without_storage)

    iphone_match = re.search(r"(?:iphone|آیفون|ایفون)\s*(\d+)(?:\s*(pro|max|plus))?", normalized)
    is_case = any(word in normalized for word in ("قاب", "کاور", "cover", "case"))
    if iphone_match:
        model = iphone_match.group(1)
        suffix = f" {iphone_match.group(2)}" if iphone_match.group(2) else ""
        base_variants = [
            f"iphone {model}{suffix}",
            f"آیفون {model}{suffix}",
            f"ایفون {model}{suffix}",
            f"aifon {model}{suffix}",
        ]
        if is_case:
            for prefix in ("قاب", "کاور", "ghab", "cover", "case"):
                generated.extend(f"{prefix} {variant}" for variant in base_variants)
        else:
            generated.extend(base_variants)

    samsung_match = re.search(r"(?:galaxy\s*)?([asmz]\s*\d{2,4})", normalized)
    if samsung_match and any(word in normalized for word in ("samsung", "سامسونگ", "galaxy")):
        model = samsung_match.group(1).replace(" ", "")
        generated.extend(
            (model, f"samsung {model}", f"سامسونگ {model}", f"galaxy {model}")
        )

    return generated


def build_aliases(product: dict[str, object]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    canonical = _alias(str(product["name"]), "canonical", "manager", 10)
    if canonical:
        candidates.append(canonical)

    for keyword in product.get("keywords", []) or []:
        item = _alias(str(keyword), "keyword", "manager", 20)
        if item:
            candidates.append(item)

    for provided in product.get("aliases", []) or []:
        if isinstance(provided, str):
            item = _alias(provided, "keyword", "manager", 20)
        elif isinstance(provided, dict):
            item = _alias(
                str(provided.get("value", "")),
                str(provided.get("kind", "generated")),
                str(provided.get("source", "agent")),
                int(provided.get("priority", 50)),
            )
            if item is not None:
                item["approved"] = bool(provided.get("approved", True))
        else:
            item = None
        if item:
            candidates.append(item)

    for value in _generated_product_aliases(str(product["name"])):
        item = _alias(value, "generated", "agent", 50)
        if item:
            candidates.append(item)

    deduplicated: dict[str, dict[str, object]] = {}
    for candidate in sorted(candidates, key=lambda item: int(item["priority"])):
        normalized = str(candidate["normalized_value"])
        deduplicated.setdefault(normalized, candidate)
    return list(deduplicated.values())


def _external_key(product: dict[str, object], index: int) -> str:
    supplied = str(product.get("client_id") or "").strip()
    if supplied:
        return supplied[:100]
    digest = hashlib.sha256(
        f"{index}:{normalize_catalog_text(str(product['name']))}".encode("utf-8")
    ).hexdigest()[:12]
    return f"product-{digest}"


def _knowledge_keywords(item: dict[str, object]) -> list[str]:
    supplied = [str(value).strip() for value in item.get("keywords", []) or []]
    supplied = [value for value in supplied if value]
    if supplied:
        return list(dict.fromkeys(supplied))
    title_tokens = normalize_catalog_text(str(item["title"])).split()
    return [token for token in title_tokens if len(token) > 2 and token not in STOP_WORDS][:8]


def analyze_catalog(payload: dict[str, object]) -> tuple[dict[str, object], list[dict[str, str]]]:
    proposal: dict[str, object] = {
        "store_name": str(payload["store_name"]).strip(),
        "products": [],
        "knowledge_items": [],
    }
    warnings: list[dict[str, str]] = []
    alias_owners: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for index, raw_product in enumerate(payload.get("products", []) or []):
        product = dict(raw_product)
        product_id = product.get("product_id")
        client_id = _external_key(product, index)
        keywords = [str(value).strip() for value in product.get("keywords", []) or [] if str(value).strip()]
        category = str(product.get("category") or "").strip() or infer_category(
            str(product["name"]),
            str(product.get("description") or "") or None,
            keywords,
        )
        aliases = build_aliases({**product, "keywords": keywords})
        product_warnings: list[dict[str, str]] = []
        if not aliases:
            warning = {
                "level": "error",
                "code": "missing_alias",
                "message": f"برای «{product['name']}» هیچ عبارت قابل تشخیصی ساخته نشد.",
            }
            warnings.append(warning)
            product_warnings.append(warning)

        for alias in aliases:
            if bool(alias.get("approved", True)):
                alias_owners[str(alias["normalized_value"])].append(
                    (client_id, str(alias["value"]))
                )

        proposal["products"].append(
            {
                "client_id": client_id,
                "product_id": int(product_id) if product_id else None,
                "name": str(product["name"]).strip(),
                "description": str(product.get("description") or "").strip() or None,
                "price": float(product["price"]),
                "is_available": bool(product.get("is_available", True)),
                "keywords": keywords,
                "category": category,
                "aliases": aliases,
                "warnings": product_warnings,
            }
        )

    for normalized, owners in alias_owners.items():
        product_keys = {owner[0] for owner in owners}
        if len(product_keys) <= 1:
            continue
        names = "، ".join(sorted({owner[1] for owner in owners}))
        warnings.append(
            {
                "level": "error",
                "code": "alias_conflict",
                "message": f"عبارت «{names}» برای چند محصول استفاده شده است؛ یکی را تغییر دهید.",
                "normalized_value": normalized,
            }
        )

    seen_knowledge: set[tuple[str, str]] = set()
    for index, raw_item in enumerate(payload.get("knowledge_items", []) or []):
        item = dict(raw_item)
        kind = str(item.get("kind", "faq"))
        title = str(item["title"]).strip()
        normalized_title = normalize_catalog_text(title)
        key = (kind, normalized_title)
        if key in seen_knowledge:
            warnings.append(
                {
                    "level": "error",
                    "code": "duplicate_knowledge",
                    "message": f"پاسخ «{title}» بیش از یک بار وارد شده است.",
                }
            )
        seen_knowledge.add(key)
        proposal["knowledge_items"].append(
            {
                "client_id": str(item.get("client_id") or f"knowledge-{index + 1}"),
                "kind": kind,
                "title": title,
                "normalized_title": normalized_title,
                "answer": str(item["answer"]).strip(),
                "keywords": _knowledge_keywords(item),
                "priority": int(item.get("priority", 100)),
            }
        )

    proposal["warnings"] = warnings
    return proposal, warnings


def create_training_draft(
    db: Session,
    payload: dict[str, object],
) -> tuple[TrainingDraft, list[dict[str, str]]]:
    store = ensure_default_store(db, str(payload["store_name"]))
    store.name = str(payload["store_name"]).strip()
    proposal, warnings = analyze_catalog(payload)
    draft = TrainingDraft(
        store_id=store.id,
        source_type="manual",
        source_payload=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        draft_payload=proposal,
        status="review",
    )
    db.add(draft)
    db.flush()
    db.add(
        AdminAuditLog(
            store_id=store.id,
            action="draft_analyzed",
            entity_type="training_draft",
            entity_id=str(draft.id),
            details_json={"warning_count": len(warnings)},
        )
    )
    db.commit()
    db.refresh(draft)
    return draft, warnings


def update_training_draft(
    db: Session,
    draft_id: int,
    payload: dict[str, object],
) -> tuple[TrainingDraft, list[dict[str, str]]]:
    draft = db.scalar(select(TrainingDraft).where(TrainingDraft.id == draft_id))
    if draft is None:
        raise LookupError("پیش‌نویس پیدا نشد")
    if draft.status == "published":
        raise CatalogPublishError("نسخه منتشرشده قابل ویرایش نیست؛ پیش‌نویس جدید بسازید")
    proposal, warnings = analyze_catalog(payload)
    draft.source_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    draft.draft_payload = proposal
    draft.status = "review"
    draft.error_message = None
    db.add(
        AdminAuditLog(
            store_id=draft.store_id,
            action="draft_updated",
            entity_type="training_draft",
            entity_id=str(draft.id),
            details_json={"warning_count": len(warnings)},
        )
    )
    db.commit()
    db.refresh(draft)
    return draft, warnings


def _blocking_warnings(warnings: list[dict[str, str]]) -> list[dict[str, str]]:
    return [warning for warning in warnings if warning.get("level") == "error"]


def publish_training_draft(db: Session, draft_id: int) -> KnowledgeVersion:
    draft = db.scalar(
        select(TrainingDraft)
        .where(TrainingDraft.id == draft_id)
        .options(joinedload(TrainingDraft.published_version))
    )
    if draft is None:
        raise LookupError("پیش‌نویس پیدا نشد")
    if draft.published_version is not None:
        return draft.published_version

    proposal, warnings = analyze_catalog(dict(draft.draft_payload))
    blocking = _blocking_warnings(warnings)
    if blocking:
        raise CatalogPublishError(blocking[0]["message"])

    store = db.get(Store, draft.store_id)
    if store is None:
        raise CatalogPublishError("فروشگاه پیدا نشد")

    canonical = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    next_version = (
        db.scalar(
            select(func.max(KnowledgeVersion.version_number)).where(
                KnowledgeVersion.store_id == store.id
            )
        )
        or 0
    ) + 1
    version = KnowledgeVersion(
        store_id=store.id,
        version_number=next_version,
        source_draft_id=draft.id,
        content_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )
    db.add(version)
    db.flush()

    category_by_name: dict[str, ProductCategory] = {}
    active_product_by_key: dict[str, int] = {}
    if store.active_version_id:
        active_rows = db.scalars(
            select(CatalogProduct).where(
                CatalogProduct.knowledge_version_id == store.active_version_id
            )
        ).all()
        active_product_by_key = {row.external_key: row.product_id for row in active_rows}

    for sort_order, product_data in enumerate(proposal["products"]):
        product_data = dict(product_data)
        category_name = str(product_data["category"])
        normalized_category = normalize_catalog_text(category_name)
        category = category_by_name.get(normalized_category)
        if category is None:
            category = ProductCategory(
                knowledge_version_id=version.id,
                name=category_name,
                normalized_name=normalized_category,
                sort_order=len(category_by_name),
            )
            db.add(category)
            db.flush()
            category_by_name[normalized_category] = category

        product_id = product_data.get("product_id") or active_product_by_key.get(
            str(product_data["client_id"])
        )
        product = db.get(Product, int(product_id)) if product_id else None
        if product is None:
            product = Product(
                name=str(product_data["name"]),
                description=product_data.get("description"),
                price=float(product_data["price"]),
                is_available=bool(product_data["is_available"]),
            )
            db.add(product)
            db.flush()
        else:
            product.name = str(product_data["name"])
            product.description = product_data.get("description")
            product.price = float(product_data["price"])
            product.is_available = bool(product_data["is_available"])

        catalog_product = CatalogProduct(
            knowledge_version_id=version.id,
            product_id=product.id,
            category_id=category.id,
            external_key=str(product_data["client_id"]),
            name=str(product_data["name"]),
            description=product_data.get("description"),
            price=float(product_data["price"]),
            is_available=bool(product_data["is_available"]),
            sort_order=sort_order,
        )
        db.add(catalog_product)
        db.flush()
        for alias_data in product_data.get("aliases", []):
            alias_data = dict(alias_data)
            if not bool(alias_data.get("approved", True)):
                continue
            db.add(
                ProductAlias(
                    catalog_product_id=catalog_product.id,
                    value=str(alias_data["value"]),
                    normalized_value=normalize_catalog_text(str(alias_data["value"])),
                    kind=str(alias_data.get("kind", "generated")),
                    priority=int(alias_data.get("priority", 100)),
                )
            )

    for item_data in proposal["knowledge_items"]:
        item_data = dict(item_data)
        db.add(
            KnowledgeItem(
                knowledge_version_id=version.id,
                kind=str(item_data["kind"]),
                title=str(item_data["title"]),
                normalized_title=normalize_catalog_text(str(item_data["title"])),
                answer=str(item_data["answer"]),
                keywords=[str(value) for value in item_data.get("keywords", [])],
                priority=int(item_data.get("priority", 100)),
            )
        )

    store.active_version_id = version.id
    store.status = "active"
    store.updated_at = datetime.now(UTC)
    draft.draft_payload = proposal
    draft.status = "published"
    db.add(
        AdminAuditLog(
            store_id=store.id,
            action="catalog_published",
            entity_type="knowledge_version",
            entity_id=str(version.id),
            details_json={"version_number": next_version, "source_draft_id": draft.id},
        )
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(version)
    return version


def serialize_draft(draft: TrainingDraft | None) -> dict[str, object] | None:
    if draft is None:
        return None
    return {
        "id": draft.id,
        "status": draft.status,
        "payload": draft.draft_payload,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def _active_catalog_payload(db: Session, store: Store) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not store.active_version_id:
        products = db.scalars(select(Product).order_by(Product.id)).all()
        faqs = db.scalars(select(FAQ).where(FAQ.is_active.is_(True)).order_by(FAQ.id)).all()
        return (
            [
                {
                    "client_id": f"legacy-{product.id}",
                    "product_id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "is_available": product.is_available,
                    "keywords": [],
                    "category": None,
                    "aliases": [],
                }
                for product in products
            ],
            [
                {
                    "client_id": f"legacy-faq-{faq.id}",
                    "kind": "faq",
                    "title": faq.question,
                    "answer": faq.answer,
                    "keywords": [],
                    "priority": 100,
                }
                for faq in faqs
            ],
        )

    catalog_rows = db.scalars(
        select(CatalogProduct)
        .where(CatalogProduct.knowledge_version_id == store.active_version_id)
        .options(
            joinedload(CatalogProduct.category),
            selectinload(CatalogProduct.aliases),
        )
        .order_by(CatalogProduct.sort_order, CatalogProduct.id)
    ).all()
    knowledge_rows = db.scalars(
        select(KnowledgeItem)
        .where(KnowledgeItem.knowledge_version_id == store.active_version_id)
        .order_by(KnowledgeItem.priority, KnowledgeItem.id)
    ).all()
    return (
        [
            {
                "client_id": row.external_key,
                "product_id": row.product_id,
                "name": row.name,
                "description": row.description,
                "price": row.price,
                "is_available": row.is_available,
                "keywords": [alias.value for alias in row.aliases if alias.kind == "keyword"],
                "category": row.category.name if row.category else None,
                "aliases": [
                    {
                        "value": alias.value,
                        "normalized_value": alias.normalized_value,
                        "kind": alias.kind,
                        "priority": alias.priority,
                        "source": "published",
                        "approved": True,
                    }
                    for alias in sorted(row.aliases, key=lambda item: (item.priority, item.id))
                ],
            }
            for row in catalog_rows
        ],
        [
            {
                "client_id": f"knowledge-{row.id}",
                "kind": row.kind,
                "title": row.title,
                "answer": row.answer,
                "keywords": row.keywords,
                "priority": row.priority,
            }
            for row in knowledge_rows
        ],
    )


def get_admin_state(db: Session) -> dict[str, object]:
    store = ensure_default_store(db)
    db.commit()
    latest_draft = db.scalar(
        select(TrainingDraft)
        .where(TrainingDraft.store_id == store.id)
        .order_by(TrainingDraft.id.desc())
    )
    active_version = db.get(KnowledgeVersion, store.active_version_id) if store.active_version_id else None
    products, knowledge_items = _active_catalog_payload(db, store)
    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "slug": store.slug,
            "status": store.status,
        },
        "active_version": (
            {
                "id": active_version.id,
                "version_number": active_version.version_number,
                "published_at": active_version.published_at,
            }
            if active_version
            else None
        ),
        "products": products,
        "knowledge_items": knowledge_items,
        "latest_draft": serialize_draft(latest_draft),
    }

