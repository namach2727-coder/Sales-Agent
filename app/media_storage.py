from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Product, ProductMediaAsset, SocialContentDraft, Store


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
JPEG_PREFIX = "data:image/jpeg;base64,"
JPEG_SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}


def media_root(settings: Settings) -> Path:
    configured = Path(settings.media_storage_root)
    root = configured if configured.is_absolute() else PROJECT_ROOT / configured
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Read JPEG dimensions without trusting the filename or browser MIME type."""
    if len(data) < 12 or not data.startswith(b"\xff\xd8\xff") or not data.endswith(b"\xff\xd9"):
        raise ValueError("فایل ارسال‌شده یک تصویر JPEG معتبر نیست.")

    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA:
            break
        if offset + 2 > len(data):
            break
        segment_length = int.from_bytes(data[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in JPEG_SOF_MARKERS and segment_length >= 7:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            if width < 1 or height < 1:
                break
            return width, height
        offset += segment_length
    raise ValueError("ابعاد تصویر قابل تشخیص نیست؛ یک تصویر دیگر انتخاب کنید.")


def decode_manager_jpeg(data_url: str) -> tuple[bytes, int, int]:
    if not data_url.startswith(JPEG_PREFIX):
        raise ValueError("تصویر باید به فرمت JPEG آماده شده باشد.")
    encoded = data_url[len(JPEG_PREFIX) :]
    if len(encoded) > (MAX_IMAGE_BYTES * 4 // 3) + 16:
        raise ValueError("حجم تصویر بیشتر از ۸ مگابایت است.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("داده تصویر معتبر نیست.") from exc
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("حجم تصویر باید کمتر از ۸ مگابایت باشد.")
    width, height = jpeg_dimensions(data)
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError("ابعاد تصویر بیش از حد بزرگ است.")
    return data, width, height


def save_product_image(
    db: Session,
    settings: Settings,
    store: Store,
    product: Product,
    original_filename: str,
    data_url: str,
) -> ProductMediaAsset:
    data, width, height = decode_manager_jpeg(data_url)
    digest = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(
        select(ProductMediaAsset).where(
            ProductMediaAsset.store_id == store.id,
            ProductMediaAsset.product_id == product.id,
            ProductMediaAsset.sha256 == digest,
            ProductMediaAsset.status == "ready",
        )
    )
    if duplicate is not None:
        return duplicate

    asset_id = str(uuid.uuid4())
    storage_key = f"store-{store.id}/{asset_id}.jpg"
    root = media_root(settings)
    target = (root / storage_key).resolve()
    if root not in target.parents:
        raise ValueError("مسیر ذخیره تصویر معتبر نیست.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    safe_name = Path(original_filename or "product.jpg").name[:255] or "product.jpg"
    asset = ProductMediaAsset(
        id=asset_id,
        store_id=store.id,
        product_id=product.id,
        storage_key=storage_key,
        original_filename=safe_name,
        content_type="image/jpeg",
        byte_size=len(data),
        width=width,
        height=height,
        sha256=digest,
        status="ready",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def resolve_asset_path(asset: ProductMediaAsset, settings: Settings) -> Path:
    root = media_root(settings)
    path = (root / asset.storage_key).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="تصویر پیدا نشد.")
    return path


def delete_product_image(db: Session, asset: ProductMediaAsset, settings: Settings) -> None:
    referenced = db.scalar(
        select(SocialContentDraft.id).where(
            SocialContentDraft.media_asset_id == asset.id,
            SocialContentDraft.status.in_(("approved", "publishing", "published")),
        )
    )
    if referenced is not None:
        raise ValueError("این تصویر در یک محتوای تأییدشده استفاده شده و قابل حذف نیست.")
    try:
        resolve_asset_path(asset, settings).unlink(missing_ok=True)
    except HTTPException:
        pass
    asset.status = "deleted"
    db.commit()


def _signature_payload(asset_id: str, expires: int) -> bytes:
    return f"{asset_id}:{expires}".encode("utf-8")


def _public_media_signature(asset_id: str, expires: int, secret: str) -> str:
    """Return a version-marked signature while keeping the HMAC itself unchanged."""
    digest = hmac.new(
        secret.encode("utf-8"), _signature_payload(asset_id, expires), hashlib.sha256
    ).hexdigest()
    return f"{digest}.v1"


def create_public_media_url(
    asset_id: str,
    settings: Settings,
    *,
    lifetime_seconds: int = 3600,
) -> str:
    base_url = settings.public_media_base_url.strip().rstrip("/")
    secret = settings.media_signing_secret.strip()
    if not base_url or not secret or secret.lower() == "replace-me-with-a-long-random-secret":
        raise ValueError("میزبانی عمومی امن تصاویر هنوز تنظیم نشده است.")
    expires = int(time.time()) + lifetime_seconds
    signature = _public_media_signature(asset_id, expires, secret)
    return f"{base_url}/media/publish/{quote(asset_id)}?exp={expires}&sig={signature}"


def validate_public_media_signature(
    asset_id: str,
    expires: int,
    signature: str,
    settings: Settings,
) -> None:
    if expires < int(time.time()) or expires > int(time.time()) + 7200:
        raise HTTPException(status_code=403, detail="Media link expired")
    secret = settings.media_signing_secret.strip()
    if not secret:
        raise HTTPException(status_code=404, detail="Not found")
    expected = _public_media_signature(asset_id, expires, secret)
    # Links generated before the version marker was introduced remain valid for
    # their short lifetime, avoiding a deployment-time publishing interruption.
    legacy_expected = expected.removesuffix(".v1")
    if not (
        hmac.compare_digest(expected, signature)
        or hmac.compare_digest(legacy_expected, signature)
    ):
        raise HTTPException(status_code=403, detail="Invalid media link")
