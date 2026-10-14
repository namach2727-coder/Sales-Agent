from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.media_storage import resolve_asset_path, validate_public_media_signature
from app.object_media_storage import presigned_image_url
from app.models import ProductMediaAsset


router = APIRouter(tags=["instagram-publishing"])


@router.get("/media/publish/{asset_id}", include_in_schema=False)
def public_product_image(
    asset_id: str,
    exp: int = Query(..., ge=1),
    sig: str = Query(..., min_length=32, max_length=128),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    validate_public_media_signature(asset_id, exp, sig, settings)
    asset = db.get(ProductMediaAsset, asset_id)
    if asset is None or asset.status != "ready":
        raise HTTPException(status_code=404, detail="Not found")
    if settings.media_storage_backend == "s3":
        # Revalidate our HMAC before issuing a short-lived private-bucket URL.
        import time

        ttl = max(1, min(900, exp - int(time.time())))
        response = RedirectResponse(
            presigned_image_url(settings, asset.storage_key, ttl_seconds=ttl),
            status_code=302,
        )
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    response = FileResponse(
        resolve_asset_path(asset, settings),
        media_type="image/jpeg",
        filename=None,
    )
    response.headers["Cache-Control"] = "public, max-age=900"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = "inline"
    return response
