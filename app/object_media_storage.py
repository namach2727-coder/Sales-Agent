"""Private S3-compatible media storage (R2 or equivalent), opt-in per environment.

This module deliberately does not create buckets, make objects public, or
retrieve credentials from outside the hosting environment.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from botocore.config import Config

from app.config import Settings


_MEDIA_KEY = re.compile(r"^store-[1-9][0-9]*/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$")
_PREFIX = re.compile(r"^[a-z0-9][a-z0-9/_-]{0,63}$")


def _configuration(settings: Settings) -> tuple[str, str, str]:
    endpoint = settings.media_s3_endpoint_url.strip().rstrip("/")
    url = urlsplit(endpoint)
    if (
        url.scheme != "https"
        or not url.netloc
        or url.username is not None
        or url.password is not None
        or url.path
        or url.query
        or url.fragment
    ):
        raise ValueError("MEDIA_S3_ENDPOINT_URL must be a credential-free HTTPS origin")

    bucket = settings.media_s3_bucket.strip()
    prefix = settings.media_s3_prefix.strip("/")
    if not bucket or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise ValueError("MEDIA_S3_BUCKET must be a valid private bucket name")
    if not _PREFIX.fullmatch(prefix) or ".." in prefix or "//" in prefix:
        raise ValueError("MEDIA_S3_PREFIX must be a safe, nonempty environment-specific prefix")
    if not settings.media_s3_access_key_id.strip() or not settings.media_s3_secret_access_key.get_secret_value().strip():
        raise ValueError("S3 media credentials are not configured")
    return endpoint, bucket, prefix


def object_key(settings: Settings, storage_key: str) -> str:
    _, _, prefix = _configuration(settings)
    if not _MEDIA_KEY.fullmatch(storage_key):
        raise ValueError("Invalid product-media storage key")
    return f"{prefix}/{storage_key}"


def _client(settings: Settings):
    # Imported lazily to avoid loading the S3 client for local-only workflows.
    import boto3

    endpoint, _, _ = _configuration(settings)
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=settings.media_s3_region.strip() or "auto",
        aws_access_key_id=settings.media_s3_access_key_id.strip(),
        aws_secret_access_key=settings.media_s3_secret_access_key.get_secret_value(),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def put_image(settings: Settings, storage_key: str, data: bytes, sha256: str) -> None:
    key = object_key(settings, storage_key)
    _client(settings).put_object(
        Bucket=settings.media_s3_bucket.strip(),
        Key=key,
        Body=data,
        ContentType="image/jpeg",
        Metadata={"sha256": sha256},
        CacheControl="private, no-store",
    )


def delete_image(settings: Settings, storage_key: str) -> None:
    key = object_key(settings, storage_key)
    _client(settings).delete_object(Bucket=settings.media_s3_bucket.strip(), Key=key)


def presigned_image_url(settings: Settings, storage_key: str, *, ttl_seconds: int) -> str:
    if not 1 <= ttl_seconds <= 900:
        raise ValueError("S3 media download expiry is outside the allowed range")
    key = object_key(settings, storage_key)
    return _client(settings).generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.media_s3_bucket.strip(), "Key": key},
        ExpiresIn=ttl_seconds,
        HttpMethod="GET",
    )
