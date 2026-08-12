from __future__ import annotations

import hashlib

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.content_generation import active_catalog_product, content_source_hash
from app.media_storage import create_public_media_url
from app.module_catalog import module_enabled
from app.models import (
    InstagramMediaProduct,
    InstagramPublishJob,
    SocialContentDraft,
    Store,
    utc_now,
)


class InstagramContentPublisher:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def account_url(self) -> str:
        return (
            f"https://graph.instagram.com/{self.settings.meta_api_version}/"
            f"{self.settings.meta_ig_user_id}"
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.meta_access_token}",
            "Content-Type": "application/json",
        }

    async def publish_image(
        self,
        *,
        image_url: str,
        caption: str,
        alt_text: str,
    ) -> dict[str, str | None]:
        if not self.settings.meta_send_enabled:
            raise RuntimeError("Meta outbound mutations are disabled")
        async with httpx.AsyncClient(timeout=30.0) as client:
            container_response = await client.post(
                f"{self.account_url}/media",
                headers=self.headers,
                json={
                    "image_url": image_url,
                    "caption": caption,
                    "alt_text": alt_text,
                },
            )
            container_response.raise_for_status()
            container_id = str(container_response.json().get("id") or "")
            if not container_id:
                raise RuntimeError("Meta شناسه آماده‌سازی پست را برنگرداند.")

            publish_response = await client.post(
                f"{self.account_url}/media_publish",
                headers=self.headers,
                json={"creation_id": container_id},
            )
            publish_response.raise_for_status()
            media_id = str(publish_response.json().get("id") or "")
            if not media_id:
                raise RuntimeError("Meta شناسه پست منتشرشده را برنگرداند.")

            permalink: str | None = None
            try:
                detail_response = await client.get(
                    f"https://graph.instagram.com/{self.settings.meta_api_version}/{media_id}",
                    headers=self.headers,
                    params={"fields": "permalink"},
                )
                detail_response.raise_for_status()
                permalink = detail_response.json().get("permalink")
            except httpx.HTTPError:
                # The post is already live; a missing permalink must not cause a
                # blind retry that could duplicate it.
                permalink = None

            return {
                "container_id": container_id,
                "media_id": media_id,
                "permalink": str(permalink) if permalink else None,
            }


def _publish_readiness(settings: Settings) -> tuple[bool, str]:
    if not settings.meta_send_enabled:
        return False, "Meta outbound mutations are disabled."
    if not settings.meta_content_publish_enabled:
        return False, "انتشار واقعی هنوز فعال نشده است؛ ابتدا مجوز انتشار Meta را اضافه کنید."
    if not settings.meta_access_token.strip() or not settings.meta_ig_user_id.strip():
        return False, "توکن و شناسه حساب اینستاگرام برای انتشار آماده نیست."
    if not settings.public_media_base_url.strip().startswith("https://"):
        return False, "برای انتشار، تصاویر باید روی یک آدرس دائمی و امن HTTPS قرار بگیرند."
    if len(settings.media_signing_secret.strip()) < 20:
        return False, "میزبانی عمومی امن تصاویر هنوز تنظیم نشده است."
    return True, ""


def publishing_status(settings: Settings) -> dict[str, object]:
    ready, reason = _publish_readiness(settings)
    return {
        "ready": ready,
        "reason": reason,
        "permission_required": "instagram_business_content_publish",
        "public_media_configured": bool(settings.public_media_base_url.strip()),
    }


async def publish_content_draft(
    db: Session,
    settings: Settings,
    store: Store,
    draft: SocialContentDraft,
) -> InstagramPublishJob:
    # Keep the commercial entitlement check next to the irreversible Meta call.
    # A route-level check alone can be bypassed by future internal callers.
    if not module_enabled(db, store, "instagram_publish"):
        raise RuntimeError(
            "ماژول انتشار پست اینستاگرام برای این فروشگاه فعال نیست."
        )
    if draft.store_id != store.id:
        raise ValueError("این محتوا به فروشگاه جاری تعلق ندارد.")
    if draft.status not in {"approved", "failed", "published"}:
        raise ValueError("ابتدا متن و تصویر را تأیید کنید.")
    if draft.status == "published":
        job = db.scalar(
            select(InstagramPublishJob).where(
                InstagramPublishJob.content_draft_id == draft.id
            )
        )
        if job is None:
            raise RuntimeError("سابقه انتشار این محتوا پیدا نشد.")
        return job
    if content_source_hash(draft.product, draft.media_asset) != draft.source_hash:
        raise RuntimeError("اطلاعات محصول تغییر کرده؛ متن را دوباره تولید و تأیید کنید.")
    if active_catalog_product(db, store, draft.product_id) is None:
        raise RuntimeError("قبل از انتشار پست، اطلاعات این محصول را برای ایجنت فعال کنید.")

    ready, reason = _publish_readiness(settings)
    if not ready:
        raise RuntimeError(reason)

    key = hashlib.sha256(
        f"{store.id}:{draft.id}:{draft.source_hash}".encode("utf-8")
    ).hexdigest()
    job = db.scalar(
        select(InstagramPublishJob).where(
            InstagramPublishJob.content_draft_id == draft.id
        )
    )
    if job is None:
        job = InstagramPublishJob(
            store_id=store.id,
            content_draft_id=draft.id,
            idempotency_key=key,
            status="queued",
        )
        db.add(job)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            job = db.scalar(
                select(InstagramPublishJob).where(
                    InstagramPublishJob.content_draft_id == draft.id
                )
            )
            if job is None:
                raise
    if job.status == "published":
        return job
    if job.meta_media_id:
        # Meta already returned a live media ID. Never blindly retry the publish
        # call just because fetching the permalink failed.
        job.status = "published"
        draft.status = "published"
        draft.published_at = utc_now()
        db.commit()
        return job

    job.status = "publishing"
    job.attempt_count += 1
    job.error_message = None
    draft.status = "publishing"
    db.commit()

    publisher = InstagramContentPublisher(settings)
    try:
        hashtag_line = " ".join(draft.hashtags or [])
        caption_limit = 2200 - (len(hashtag_line) + 2 if hashtag_line else 0)
        publish_caption = "\n\n".join(
            part for part in (draft.caption[: max(0, caption_limit)], hashtag_line) if part
        )
        result = await publisher.publish_image(
            image_url=create_public_media_url(draft.media_asset_id, settings),
            caption=publish_caption,
            alt_text=draft.alt_text,
        )
        job.meta_container_id = result.get("container_id")
        job.meta_media_id = result.get("media_id")
        job.permalink = result.get("permalink")
        job.status = "published"
        draft.status = "published"
        draft.published_at = utc_now()

        existing_mapping = db.scalar(
            select(InstagramMediaProduct).where(
                InstagramMediaProduct.media_id == job.meta_media_id
            )
        )
        if existing_mapping is None:
            db.add(
                InstagramMediaProduct(
                    media_id=str(job.meta_media_id),
                    product_id=draft.product_id,
                    media_product_type="FEED",
                    permalink=job.permalink,
                )
            )
        db.commit()
        db.refresh(job)
        return job
    except httpx.TimeoutException as exc:
        # A timeout may happen after Meta accepted media_publish. Mark the job
        # unknown and require reconciliation instead of risking a duplicate post.
        job.status = "unknown"
        job.error_message = "پاسخ نهایی Meta دریافت نشد؛ قبل از تلاش دوباره پیج را بررسی کنید."
        draft.status = "unknown"
        db.commit()
        raise RuntimeError(job.error_message) from exc
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        job.status = "failed"
        job.error_message = str(exc)[:1000]
        draft.status = "failed"
        db.commit()
        raise RuntimeError("انتشار در اینستاگرام انجام نشد؛ پیش‌نویس شما محفوظ است.") from exc


def serialize_publish_job(job: InstagramPublishJob) -> dict[str, object]:
    return {
        "id": job.id,
        "content_draft_id": job.content_draft_id,
        "status": job.status,
        "media_id": job.meta_media_id,
        "permalink": job.permalink,
        "attempt_count": job.attempt_count,
        "error_message": job.error_message,
    }
