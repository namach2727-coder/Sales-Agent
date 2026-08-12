import asyncio
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.catalog_training import ensure_default_store
from app.database import Base, get_db
from app.instagram_publishing import InstagramContentPublisher
from app.main import app, settings
from app.media_storage import create_public_media_url
from app.models import (
    InstagramMediaProduct,
    InstagramPublishJob,
    ProductMediaAsset,
    Store,
    StoreModule,
)
from app.module_catalog import ensure_store_modules
from app.seed import seed_demo_catalog


LOCAL_ORIGIN = "http://127.0.0.1:8000"
MUTATION_HEADERS = {"origin": LOCAL_ORIGIN, "sec-fetch-site": "same-origin"}
ONE_PIXEL_JPEG = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////"
    "//////////////////////////////////////////2wBDAf//////////////////////////"
    "//////////////////////////////////////////////////////////wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oA"
    "DAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAA"
    "AAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEB"
    "PwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAA"
    "AAAP/aAAgBAQABPyF//9oADAMBAAIAAwAAABAf/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgB"
    "AwEBPxB//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPxB//8QAFBABAAAAAAAAAAAAAAAA"
    "AAAAAP/aAAgBAQABPxB//9k="
)


@pytest.fixture
def content_client(monkeypatch, tmp_path):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    with TestSession() as db:
        seed_demo_catalog(db)
        store = ensure_default_store(db)
        ensure_store_modules(db, store, activate_legacy_defaults=True)
        db.commit()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "media_storage_root", str(tmp_path / "media"))
    monkeypatch.setattr(settings, "meta_content_publish_enabled", False)
    monkeypatch.setattr(settings, "public_media_base_url", "")
    monkeypatch.setattr(settings, "media_signing_secret", "")
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            base_url=LOCAL_ORIGIN,
            client=("127.0.0.1", 51000),
        ) as client:
            yield client, TestSession
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


def upload_image(client: TestClient, product_id: int) -> dict:
    response = client.post(
        f"/admin/api/products/{product_id}/media",
        json={
            "filename": "../product.png",
            "data_url": f"data:image/jpeg;base64,{ONE_PIXEL_JPEG}",
        },
        headers=MUTATION_HEADERS,
    )
    assert response.status_code == 200, response.text
    return response.json()["asset"]


def test_content_publisher_fails_closed_before_network(monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_send_enabled", False)
    monkeypatch.setattr(settings, "meta_content_publish_enabled", True)

    class ForbiddenClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("network client must not be constructed")

    monkeypatch.setattr(httpx, "AsyncClient", ForbiddenClient)
    with pytest.raises(RuntimeError, match="outbound mutations are disabled"):
        asyncio.run(
            InstagramContentPublisher(settings).publish_image(
                image_url="https://media.example.test/image.jpg",
                caption="caption",
                alt_text="alt text",
            )
        )


def activate_single_product(client: TestClient, product: dict) -> None:
    analyzed = client.post(
        "/admin/api/drafts/analyze",
        json={
            "store_name": "فروشگاه آزمایشی",
            "products": [
                {
                    "product_id": product["id"],
                    "client_id": f"product-{product['id']}",
                    "name": product["name"],
                    "description": product.get("description"),
                    "price": product["price"],
                    "is_available": product["is_available"],
                    "keywords": ["کلید فروش تست"],
                }
            ],
            "knowledge_items": [],
        },
        headers=MUTATION_HEADERS,
    )
    assert analyzed.status_code == 200, analyzed.text
    draft_id = analyzed.json()["draft"]["id"]
    published = client.post(
        f"/admin/api/drafts/{draft_id}/publish",
        json={},
        headers=MUTATION_HEADERS,
    )
    assert published.status_code == 200, published.text


def test_content_studio_loads_products_and_is_local_only(content_client) -> None:
    client, _ = content_client
    state = client.get("/admin/api/content-studio")
    assert state.status_code == 200
    assert len(state.json()["products"]) == 3
    assert state.json()["publishing"]["ready"] is False
    assert state.json()["publishing"]["permission_required"] == (
        "instagram_business_content_publish"
    )


def test_image_upload_is_validated_private_and_previewable(content_client) -> None:
    client, TestSession = content_client
    product = client.get("/admin/api/content-studio").json()["products"][0]
    asset = upload_image(client, product["id"])

    assert asset["filename"] == "product.png"
    assert asset["width"] == 1
    assert asset["height"] == 1
    preview = client.get(asset["preview_url"])
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/jpeg"
    assert preview.headers["cache-control"] == "no-store"

    invalid = client.post(
        f"/admin/api/products/{product['id']}/media",
        json={"filename": "fake.jpg", "data_url": "data:image/jpeg;base64," + ("A" * 100)},
        headers=MUTATION_HEADERS,
    )
    assert invalid.status_code == 422
    with TestSession() as db:
        assert db.scalar(select(func.count(ProductMediaAsset.id))) == 1


def test_generate_edit_approve_and_block_unconfigured_publish(content_client) -> None:
    client, _ = content_client
    product = client.get("/admin/api/content-studio").json()["products"][0]
    asset = upload_image(client, product["id"])
    generated = client.post(
        "/admin/api/content-drafts/generate",
        json={"product_id": product["id"], "media_asset_id": asset["id"]},
        headers=MUTATION_HEADERS,
    )
    assert generated.status_code == 200
    draft = generated.json()["draft"]
    assert product["name"] in draft["caption"]
    assert "قیمت" in draft["caption"]
    assert draft["hashtags"]
    assert product["name"] in draft["sales_keywords"]

    edited = client.put(
        f"/admin/api/content-drafts/{draft['id']}",
        json={
            "caption": draft["caption"] + "\nارسال رایگان آزمایشی",
            "hashtags": ["#تست_فروش"],
            "alt_text": "تصویر آزمایشی محصول",
            "expected_revision": draft["revision"],
        },
        headers=MUTATION_HEADERS,
    )
    assert edited.status_code == 200
    draft = edited.json()["draft"]
    approved = client.post(
        f"/admin/api/content-drafts/{draft['id']}/approve",
        json={"expected_revision": draft["revision"]},
        headers=MUTATION_HEADERS,
    )
    assert approved.status_code == 200
    draft = approved.json()["draft"]
    assert draft["status"] == "approved"

    blocked = client.post(
        f"/admin/api/content-drafts/{draft['id']}/publish",
        json={"expected_revision": draft["revision"], "confirmation": "publish"},
        headers=MUTATION_HEADERS,
    )
    assert blocked.status_code == 403
    assert "ماژول" in blocked.json()["detail"]


def test_signed_public_media_link_rejects_tampering(content_client, monkeypatch) -> None:
    client, _ = content_client
    product = client.get("/admin/api/content-studio").json()["products"][0]
    asset = upload_image(client, product["id"])
    monkeypatch.setattr(settings, "public_media_base_url", LOCAL_ORIGIN)
    monkeypatch.setattr(settings, "media_signing_secret", "test-signing-secret-that-is-long")
    url = create_public_media_url(asset["id"], settings)
    parsed = urlsplit(url)

    valid = client.get(f"{parsed.path}?{parsed.query}")
    assert valid.status_code == 200
    tampered = client.get(f"{parsed.path}?{parsed.query[:-1]}0")
    assert tampered.status_code == 403


def test_live_publish_is_idempotent_and_maps_comments(
    content_client, monkeypatch
) -> None:
    client, TestSession = content_client
    state = client.get("/admin/api/content-studio").json()
    product = state["products"][0]
    activate_single_product(client, product)
    asset = upload_image(client, product["id"])
    draft = client.post(
        "/admin/api/content-drafts/generate",
        json={"product_id": product["id"], "media_asset_id": asset["id"]},
        headers=MUTATION_HEADERS,
    ).json()["draft"]
    draft = client.post(
        f"/admin/api/content-drafts/{draft['id']}/approve",
        json={"expected_revision": draft["revision"]},
        headers=MUTATION_HEADERS,
    ).json()["draft"]

    with TestSession() as db:
        store = db.scalar(select(Store).where(Store.slug == "default"))
        assert store is not None
        publish_module = db.scalar(
            select(StoreModule).where(
                StoreModule.store_id == store.id,
                StoreModule.module_code == "instagram_publish",
            )
        )
        assert publish_module is not None
        publish_module.status = "active"
        db.commit()

    monkeypatch.setattr(settings, "meta_content_publish_enabled", True)
    monkeypatch.setattr(settings, "meta_send_enabled", False)
    monkeypatch.setattr(settings, "meta_access_token", "test-access-token")
    monkeypatch.setattr(settings, "meta_ig_user_id", "123456789")
    monkeypatch.setattr(settings, "public_media_base_url", "https://media.example.test")
    monkeypatch.setattr(settings, "media_signing_secret", "test-signing-secret-that-is-long")
    calls = {"count": 0}

    async def fake_publish(self, *, image_url, caption, alt_text):
        calls["count"] += 1
        assert image_url.startswith("https://media.example.test/media/publish/")
        assert product["name"] in caption
        return {
            "container_id": "container-1",
            "media_id": "media-1",
            "permalink": "https://www.instagram.com/p/example/",
        }

    monkeypatch.setattr(InstagramContentPublisher, "publish_image", fake_publish)
    payload = {"expected_revision": draft["revision"], "confirmation": "publish"}
    disabled = client.post(
        f"/admin/api/content-drafts/{draft['id']}/publish",
        json=payload,
        headers=MUTATION_HEADERS,
    )
    assert disabled.status_code == 409
    assert calls["count"] == 0

    monkeypatch.setattr(settings, "meta_send_enabled", True)
    first = client.post(
        f"/admin/api/content-drafts/{draft['id']}/publish",
        json=payload,
        headers=MUTATION_HEADERS,
    )
    second = client.post(
        f"/admin/api/content-drafts/{draft['id']}/publish",
        json=payload,
        headers=MUTATION_HEADERS,
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["job"]["status"] == "published"
    assert calls["count"] == 1
    with TestSession() as db:
        mapping = db.scalar(
            select(InstagramMediaProduct).where(
                InstagramMediaProduct.media_id == "media-1"
            )
        )
        assert mapping is not None
        assert mapping.product_id == product["id"]
        assert db.scalar(select(func.count(InstagramPublishJob.id))) == 1
