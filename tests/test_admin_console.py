import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.catalog_training import ensure_default_store
from app.database import Base, get_db
from app.main import app, settings
from app.models import Conversation, Customer, Order
from app.seed import seed_demo_catalog


LOCAL_ORIGIN = "http://127.0.0.1:8000"
MUTATION_HEADERS = {"origin": LOCAL_ORIGIN, "sec-fetch-site": "same-origin"}


def sample_payload(*, keyword: str = "ستاره ویژه") -> dict:
    return {
        "store_name": "فروشگاه تست مدیر",
        "products": [
            {
                "client_id": "headphone-x1",
                "name": "هدفون ستاره X1",
                "description": "هدفون بی‌سیم مشکی با یک سال ضمانت",
                "price": 1_234_000,
                "is_available": True,
                "keywords": [keyword, "setare x1"],
            }
        ],
        "knowledge_items": [
            {
                "client_id": "shipping-rule",
                "kind": "rule",
                "title": "شرایط ارسال",
                "answer": "ارسال تستی با پیک و پست انجام می‌شود.",
                "keywords": ["ارسال", "پست", "پیک"],
            }
        ],
    }


@pytest.fixture
def admin_client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    with TestSession() as db:
        seed_demo_catalog(db)
        ensure_default_store(db)
        db.commit()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "app_env", "development")
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


def test_admin_page_and_assets_are_local_and_not_cached(admin_client) -> None:
    client, _ = admin_client
    page = client.get("/admin")
    script = client.get("/static/admin.js")
    module_script = client.get("/static/admin_modules.js")

    assert page.status_code == 200
    assert page.headers["cache-control"] == "no-store"
    assert page.headers["x-frame-options"] == "DENY"
    assert 'id="analyze-button"' in page.text
    assert 'id="module-marketplace-trigger"' in page.text
    assert "آموزش دستیار فروش" in page.text
    assert script.status_code == 200
    assert module_script.status_code == 200
    assert 'fetch(url, request)' in script.text


def test_remote_client_cannot_open_admin(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    with TestClient(
        app,
        base_url=LOCAL_ORIGIN,
        client=("203.0.113.9", 51000),
    ) as client:
        response = client.get("/admin")

    assert response.status_code == 403


def test_mutations_require_same_origin(admin_client) -> None:
    client, _ = admin_client
    response = client.post("/admin/api/drafts/analyze", json=sample_payload())
    assert response.status_code == 403


def test_draft_does_not_change_agent_until_publish(admin_client) -> None:
    client, _ = admin_client
    before = client.post(
        "/chat",
        json={"instagram_user_id": "admin-before", "message": "قیمت ستاره ویژه"},
    )
    analyzed = client.post(
        "/admin/api/drafts/analyze",
        json=sample_payload(),
        headers=MUTATION_HEADERS,
    )

    assert before.status_code == 200
    assert before.json()["product"] is None
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["warnings"] == []
    proposal = body["draft"]["payload"]
    assert proposal["products"][0]["category"] == "سایر محصولات"
    assert {item["value"] for item in proposal["products"][0]["aliases"]} >= {
        "هدفون ستاره X1",
        "ستاره ویژه",
    }

    still_draft = client.post(
        "/chat",
        json={"instagram_user_id": "admin-draft", "message": "قیمت ستاره ویژه"},
    )
    assert still_draft.json()["product"] is None


def test_publish_activates_alias_catalog_and_store_knowledge(admin_client) -> None:
    client, _ = admin_client
    analyzed = client.post(
        "/admin/api/drafts/analyze",
        json=sample_payload(),
        headers=MUTATION_HEADERS,
    ).json()
    draft_id = analyzed["draft"]["id"]

    published = client.post(
        f"/admin/api/drafts/{draft_id}/publish",
        headers=MUTATION_HEADERS,
    )
    price = client.post(
        "/chat",
        json={"instagram_user_id": "admin-published", "message": "gheymat setare x1 chande"},
    )
    shipping = client.post(
        "/chat",
        json={"instagram_user_id": "admin-knowledge", "message": "ارسال با پست دارید؟"},
    )
    products = client.get("/products")

    assert published.status_code == 200
    assert published.json()["active_version"]["version_number"] == 1
    assert price.status_code == 200
    assert price.json()["product"]["name"] == "هدفون ستاره X1"
    assert "1,234,000 تومان" in price.json()["reply"]
    assert shipping.json()["reply"] == "ارسال تستی با پیک و پست انجام می‌شود."
    assert [item["name"] for item in products.json()] == ["هدفون ستاره X1"]


def test_alias_conflict_blocks_publish(admin_client) -> None:
    client, _ = admin_client
    payload = sample_payload(keyword="عبارت مشترک")
    payload["products"].append(
        {
            "client_id": "speaker-y2",
            "name": "اسپیکر Y2",
            "description": "اسپیکر همراه",
            "price": 2_000_000,
            "is_available": True,
            "keywords": ["عبارت مشترک"],
        }
    )
    analyzed = client.post(
        "/admin/api/drafts/analyze",
        json=payload,
        headers=MUTATION_HEADERS,
    )
    warnings = analyzed.json()["warnings"]
    assert any(item["code"] == "alias_conflict" for item in warnings)

    draft_id = analyzed.json()["draft"]["id"]
    publish = client.post(
        f"/admin/api/drafts/{draft_id}/publish",
        headers=MUTATION_HEADERS,
    )
    assert publish.status_code == 409
    assert "چند محصول" in publish.json()["detail"]


def test_admin_test_chat_rolls_back_sales_data(admin_client) -> None:
    client, TestSession = admin_client
    analyzed = client.post(
        "/admin/api/drafts/analyze",
        json=sample_payload(),
        headers=MUTATION_HEADERS,
    ).json()
    client.post(
        f"/admin/api/drafts/{analyzed['draft']['id']}/publish",
        headers=MUTATION_HEADERS,
    )

    with TestSession() as db:
        before = (
            db.scalar(select(func.count(Customer.id))),
            db.scalar(select(func.count(Conversation.id))),
            db.scalar(select(func.count(Order.id))),
        )

    response = client.post(
        "/admin/api/test",
        json={"message": "قیمت ستاره ویژه چنده؟"},
        headers=MUTATION_HEADERS,
    )

    with TestSession() as db:
        after = (
            db.scalar(select(func.count(Customer.id))),
            db.scalar(select(func.count(Conversation.id))),
            db.scalar(select(func.count(Order.id))),
        )

    assert response.status_code == 200
    assert response.json()["product"]["name"] == "هدفون ستاره X1"
    assert after == before
