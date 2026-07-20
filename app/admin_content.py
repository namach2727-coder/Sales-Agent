from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.admin import require_admin_mutation, require_admin_read
from app.admin_schemas import (
    ContentGenerateInput,
    ContentPublishInput,
    ContentRevisionInput,
    ContentUpdateInput,
    ProductImageUploadInput,
)
from app.catalog_runtime import list_products as list_catalog_products
from app.config import Settings, get_settings
from app.content_generation import (
    approve_content_draft,
    create_content_draft,
    default_store,
    serialize_asset,
    serialize_content_draft,
    update_content_draft,
)
from app.database import get_db
from app.instagram_publishing import (
    publish_content_draft,
    publishing_status,
    serialize_publish_job,
)
from app.media_storage import (
    delete_product_image,
    resolve_asset_path,
    save_product_image,
)
from app.models import Product, ProductMediaAsset, SocialContentDraft
from app.module_catalog import module_enabled


router = APIRouter(tags=["admin-content-studio"])


def _require_store_module(db: Session, store, code: str) -> None:
    if not module_enabled(db, store, code):
        raise HTTPException(
            status_code=403,
            detail="این قابلیت در بسته فعلی فروشگاه فعال نیست. از بخش ماژول‌ها آن را فعال کنید.",
        )


def _product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="محصول پیدا نشد.")
    return product


def _asset_or_404(db: Session, asset_id: str) -> ProductMediaAsset:
    asset = db.get(ProductMediaAsset, asset_id)
    if asset is None or asset.status != "ready":
        raise HTTPException(status_code=404, detail="تصویر پیدا نشد.")
    return asset


def _draft_or_404(db: Session, draft_id: int) -> SocialContentDraft:
    draft = db.scalar(
        select(SocialContentDraft)
        .options(
            joinedload(SocialContentDraft.product),
            joinedload(SocialContentDraft.media_asset),
        )
        .where(SocialContentDraft.id == draft_id)
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="پیش‌نویس محتوا پیدا نشد.")
    return draft


@router.get("/admin/api/content-studio", dependencies=[Depends(require_admin_read)])
def content_studio_state(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    store = default_store(db)
    _, products = list_catalog_products(db)
    if not products:
        products = list(db.scalars(select(Product).order_by(Product.id)).all())
    assets = list(
        db.scalars(
            select(ProductMediaAsset)
            .where(
                ProductMediaAsset.store_id == store.id,
                ProductMediaAsset.status == "ready",
            )
            .order_by(ProductMediaAsset.created_at.desc())
        ).all()
    )
    drafts = list(
        db.scalars(
            select(SocialContentDraft)
            .options(
                joinedload(SocialContentDraft.product),
                joinedload(SocialContentDraft.media_asset),
            )
            .where(SocialContentDraft.store_id == store.id)
            .order_by(SocialContentDraft.updated_at.desc(), SocialContentDraft.id.desc())
            .limit(30)
        ).all()
    )
    assets_by_product: dict[int, list[dict[str, object]]] = {}
    for asset in assets:
        assets_by_product.setdefault(asset.product_id, []).append(serialize_asset(asset))
    content_strategy_enabled = module_enabled(db, store, "content_strategy")
    content_review_enabled = module_enabled(db, store, "content_review")
    instagram_publish_enabled = module_enabled(db, store, "instagram_publish")
    technical_publishing = publishing_status(settings)
    if not instagram_publish_enabled:
        technical_publishing = {
            **technical_publishing,
            "ready": False,
            "reason": "ماژول انتشار پست برای این فروشگاه فعال نیست.",
            "module_required": "instagram_publish",
        }
    return {
        "store": {"id": store.id, "name": store.name},
        "active_catalog": store.active_version_id is not None,
        "publishing": technical_publishing,
        "modules": {
            "content_strategy": {"enabled": content_strategy_enabled},
            "content_review": {"enabled": content_review_enabled},
            "instagram_publish": {"enabled": instagram_publish_enabled},
        },
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "is_available": product.is_available,
                "assets": assets_by_product.get(product.id, []),
            }
            for product in products
        ],
        "drafts": [serialize_content_draft(draft) for draft in drafts],
    }


@router.post(
    "/admin/api/products/{product_id}/media",
    dependencies=[Depends(require_admin_mutation)],
)
def upload_product_media(
    product_id: int,
    payload: ProductImageUploadInput,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    store = default_store(db)
    _require_store_module(db, store, "content_strategy")
    product = _product_or_404(db, product_id)
    image_count = db.scalar(
        select(func.count(ProductMediaAsset.id)).where(
            ProductMediaAsset.store_id == store.id,
            ProductMediaAsset.product_id == product.id,
            ProductMediaAsset.status == "ready",
        )
    )
    if (image_count or 0) >= 10:
        raise HTTPException(
            status_code=409,
            detail="برای هر محصول حداکثر ۱۰ تصویر نگهداری می‌شود.",
        )
    try:
        asset = save_product_image(
            db,
            settings,
            store,
            product,
            payload.filename,
            payload.data_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"asset": serialize_asset(asset)}


@router.get(
    "/admin/api/product-media/{asset_id}/preview",
    include_in_schema=False,
    dependencies=[Depends(require_admin_read)],
)
def preview_product_media(
    asset_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    asset = _asset_or_404(db, asset_id)
    store = default_store(db)
    _require_store_module(db, store, "content_strategy")
    response = FileResponse(resolve_asset_path(asset, settings), media_type="image/jpeg")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = "inline"
    return response


@router.delete(
    "/admin/api/product-media/{asset_id}",
    dependencies=[Depends(require_admin_mutation)],
)
def remove_product_media(
    asset_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    asset = _asset_or_404(db, asset_id)
    store = default_store(db)
    _require_store_module(db, store, "content_strategy")
    try:
        delete_product_image(db, asset, settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.post(
    "/admin/api/content-drafts/generate",
    dependencies=[Depends(require_admin_mutation)],
)
def generate_content(
    payload: ContentGenerateInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    store = default_store(db)
    _require_store_module(db, store, "content_strategy")
    product = _product_or_404(db, payload.product_id)
    asset = _asset_or_404(db, payload.media_asset_id)
    try:
        draft = create_content_draft(db, store, product, asset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"draft": serialize_content_draft(_draft_or_404(db, draft.id))}


@router.put(
    "/admin/api/content-drafts/{draft_id}",
    dependencies=[Depends(require_admin_mutation)],
)
def edit_content(
    draft_id: int,
    payload: ContentUpdateInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    draft = _draft_or_404(db, draft_id)
    store = default_store(db)
    _require_store_module(db, store, "content_review")
    try:
        update_content_draft(
            db,
            draft,
            caption=payload.caption,
            hashtags=payload.hashtags,
            alt_text=payload.alt_text,
            expected_revision=payload.expected_revision,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"draft": serialize_content_draft(_draft_or_404(db, draft.id))}


@router.post(
    "/admin/api/content-drafts/{draft_id}/approve",
    dependencies=[Depends(require_admin_mutation)],
)
def approve_content(
    draft_id: int,
    payload: ContentRevisionInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    draft = _draft_or_404(db, draft_id)
    store = default_store(db)
    _require_store_module(db, store, "content_review")
    try:
        approve_content_draft(db, draft, payload.expected_revision)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"draft": serialize_content_draft(_draft_or_404(db, draft.id))}


@router.post(
    "/admin/api/content-drafts/{draft_id}/publish",
    dependencies=[Depends(require_admin_mutation)],
)
async def publish_content(
    draft_id: int,
    payload: ContentPublishInput,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    store = default_store(db)
    _require_store_module(db, store, "content_review")
    _require_store_module(db, store, "instagram_publish")
    draft = _draft_or_404(db, draft_id)
    if draft.revision != payload.expected_revision:
        raise HTTPException(status_code=409, detail="نسخه پیش‌نویس تغییر کرده است.")
    try:
        job = await publish_content_draft(db, settings, store, draft)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "draft": serialize_content_draft(_draft_or_404(db, draft.id)),
        "job": serialize_publish_job(job),
    }
