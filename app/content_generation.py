from __future__ import annotations

import hashlib
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.catalog_text import normalize_catalog_text
from app.chat import format_price
from app.models import (
    CatalogProduct,
    Product,
    ProductMediaAsset,
    SocialContentDraft,
    Store,
    utc_now,
)


MAX_CAPTION_LENGTH = 2200
MAX_HASHTAGS = 30


def default_store(db: Session) -> Store:
    store = db.scalar(select(Store).where(Store.slug == "default"))
    if store is None:
        raise ValueError("فروشگاه پیدا نشد.")
    return store


def active_catalog_product(
    db: Session, store: Store, product_id: int
) -> CatalogProduct | None:
    if store.active_version_id is None:
        return None
    return db.scalar(
        select(CatalogProduct)
        .options(
            joinedload(CatalogProduct.category),
            selectinload(CatalogProduct.aliases),
        )
        .where(
            CatalogProduct.knowledge_version_id == store.active_version_id,
            CatalogProduct.product_id == product_id,
        )
    )


def content_source_hash(product: Product, asset: ProductMediaAsset) -> str:
    snapshot = {
        "product_id": product.id,
        "name": product.name,
        "description": product.description or "",
        "price": product.price,
        "is_available": product.is_available,
        "asset_sha256": asset.sha256,
    }
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hashtag(value: str) -> str | None:
    normalized = normalize_catalog_text(value)
    normalized = re.sub(r"[^\w\u0600-\u06ff]+", "_", normalized, flags=re.UNICODE)
    normalized = normalized.strip("_")
    if len(normalized) < 2:
        return None
    return f"#{normalized[:80]}"


def _unique(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        key = normalize_catalog_text(value)
        if not value or not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def product_sales_keywords(
    db: Session, store: Store, product: Product
) -> tuple[list[str], str | None]:
    catalog_product = active_catalog_product(db, store, product.id)
    if catalog_product is None:
        return [product.name], None
    aliases = [alias.value for alias in catalog_product.aliases]
    keywords = _unique([product.name, *aliases], limit=10)
    category = catalog_product.category.name if catalog_product.category else None
    return keywords, category


def generate_social_copy(
    db: Session,
    store: Store,
    product: Product,
) -> tuple[str, list[str], str, list[str]]:
    sales_keywords, category = product_sales_keywords(db, store, product)
    trigger = min(sales_keywords, key=len) if sales_keywords else product.name
    availability = "موجود و آماده سفارش" if product.is_available else "فعلاً ناموجود"
    description = (product.description or "").strip()

    lines = [f"✨ {product.name}"]
    if description:
        lines.extend(["", description])
    lines.extend(
        [
            "",
            f"💰 قیمت: {format_price(product.price)}",
            f"📦 وضعیت: {availability}",
            "",
            (
                f"برای دریافت قیمت و ثبت سفارش، عبارت «{trigger}» را دایرکت کنید "
                "یا زیر همین پست بنویسید «قیمت»."
            ),
        ]
    )
    caption = "\n".join(lines)[:MAX_CAPTION_LENGTH]

    candidates = [store.name, product.name]
    if category:
        candidates.append(category)
    candidates.extend(sales_keywords)
    candidates.extend(["خرید آنلاین", "فروشگاه اینترنتی", "ثبت سفارش"])
    hashtags = _unique(
        [tag for item in candidates if (tag := _hashtag(item))], limit=MAX_HASHTAGS
    )
    alt_text = f"تصویر محصول {product.name}. {description}".strip()[:1000]
    return caption, hashtags, alt_text, sales_keywords


def create_content_draft(
    db: Session,
    store: Store,
    product: Product,
    asset: ProductMediaAsset,
) -> SocialContentDraft:
    if asset.store_id != store.id or asset.product_id != product.id or asset.status != "ready":
        raise ValueError("این تصویر به محصول انتخاب‌شده تعلق ندارد.")
    caption, hashtags, alt_text, sales_keywords = generate_social_copy(
        db, store, product
    )
    draft = SocialContentDraft(
        store_id=store.id,
        product_id=product.id,
        media_asset_id=asset.id,
        caption=caption,
        hashtags=hashtags,
        alt_text=alt_text,
        sales_keywords=sales_keywords,
        source_hash=content_source_hash(product, asset),
        status="draft",
        revision=1,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def update_content_draft(
    db: Session,
    draft: SocialContentDraft,
    *,
    caption: str,
    hashtags: list[str],
    alt_text: str,
    expected_revision: int,
) -> SocialContentDraft:
    if draft.status in {"publishing", "published"}:
        raise ValueError("محتوای منتشرشده قابل ویرایش نیست.")
    if draft.revision != expected_revision:
        raise RuntimeError("این پیش‌نویس در جای دیگری تغییر کرده؛ صفحه را تازه کنید.")
    clean_caption = caption.strip()
    if not clean_caption or len(clean_caption) > MAX_CAPTION_LENGTH:
        raise ValueError("متن پست باید بین ۱ تا ۲۲۰۰ نویسه باشد.")
    clean_hashtags = _unique(
        [item if item.startswith("#") else f"#{item}" for item in hashtags],
        limit=MAX_HASHTAGS,
    )
    draft.caption = clean_caption
    draft.hashtags = clean_hashtags
    draft.alt_text = alt_text.strip()[:1000]
    draft.revision += 1
    draft.status = "draft"
    draft.approved_at = None
    db.commit()
    db.refresh(draft)
    return draft


def approve_content_draft(
    db: Session, draft: SocialContentDraft, expected_revision: int
) -> SocialContentDraft:
    if draft.revision != expected_revision:
        raise RuntimeError("نسخه پیش‌نویس تغییر کرده؛ دوباره آن را بررسی کنید.")
    if draft.status == "published":
        return draft
    if content_source_hash(draft.product, draft.media_asset) != draft.source_hash:
        raise RuntimeError("اطلاعات محصول تغییر کرده؛ متن را دوباره تولید کنید.")
    draft.status = "approved"
    draft.approved_at = utc_now()
    db.commit()
    db.refresh(draft)
    return draft


def serialize_asset(asset: ProductMediaAsset) -> dict[str, object]:
    return {
        "id": asset.id,
        "product_id": asset.product_id,
        "filename": asset.original_filename,
        "width": asset.width,
        "height": asset.height,
        "byte_size": asset.byte_size,
        "status": asset.status,
        "preview_url": f"/admin/api/product-media/{asset.id}/preview",
        "created_at": asset.created_at.isoformat(),
    }


def serialize_content_draft(draft: SocialContentDraft) -> dict[str, object]:
    return {
        "id": draft.id,
        "product_id": draft.product_id,
        "product_name": draft.product.name,
        "media": serialize_asset(draft.media_asset),
        "caption": draft.caption,
        "hashtags": list(draft.hashtags or []),
        "alt_text": draft.alt_text,
        "sales_keywords": list(draft.sales_keywords or []),
        "status": draft.status,
        "revision": draft.revision,
        "approved_at": draft.approved_at.isoformat() if draft.approved_at else None,
        "published_at": draft.published_at.isoformat() if draft.published_at else None,
        "created_at": draft.created_at.isoformat(),
    }
