from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Customer, Order


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_page_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/demo")
        script_response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "دستیار فروش هوشمند" in response.text
    assert 'id="chat-form"' in response.text
    assert 'id="operator-button"' in response.text
    assert 'id="orders-view"' in response.text
    assert script_response.status_code == 200
    assert 'fetch("/chat"' in script_response.text
    assert 'fetch("/orders"' in script_response.text


def test_demo_products_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) >= 3
    assert {item["name"] for item in products} >= {
        "Apple iPhone 15 128GB",
        "Samsung Galaxy A55 256GB",
        "قاب سیلیکونی iPhone 15",
    }


def test_chat_returns_iphone_price() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"instagram_user_id": "pytest-price-user", "message": "قیمت آیفون ۱۵ چنده؟"},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["product"]["name"] == "Apple iPhone 15 128GB"
    assert "72,500,000 تومان" in result["reply"]
    assert result["needs_human"] is False


def test_chat_saves_persian_phone_number() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "instagram_user_id": "pytest-phone-user",
                "customer_name": "مشتری آزمایشی",
                "message": "شماره من ۰۹۱۲۱۲۳۴۵۶۷ است",
            },
        )

    assert response.status_code == 200
    result = response.json()
    assert result["phone_saved"] is True
    assert result["needs_human"] is True

    with SessionLocal() as db:
        customer = db.scalar(
            select(Customer).where(Customer.instagram_user_id == "pytest-phone-user")
        )
        assert customer is not None
        assert customer.phone == "09121234567"

    with TestClient(app) as client:
        leads_response = client.get("/leads")

    assert leads_response.status_code == 200
    assert any(
        lead["instagram_user_id"] == "pytest-phone-user"
        and lead["phone"] == "09121234567"
        for lead in leads_response.json()
    )


def test_chat_registers_order_with_typo_and_prevents_duplicate() -> None:
    user_id = "pytest-order-user"
    with TestClient(app) as client:
        client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "قیمت آیفون ۱۵ چنده؟"},
        )
        client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "شماره من ۰۹۱۲۱۲۳۴۵۶۷ است"},
        )
        client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "این یک پیام نامرتبط آزمایشی است"},
        )
        order_response = client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "همینجا سقارش من را ثبت کن"},
        )
        duplicate_response = client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "سفارشم را دوباره ثبت کن"},
        )
        orders_response = client.get("/orders")

    assert order_response.status_code == 200
    order_result = order_response.json()
    assert order_result["order"]["product_name"] == "Apple iPhone 15 128GB"
    assert order_result["order"]["status"] == "pending"
    assert order_result["needs_human"] is True
    assert duplicate_response.json()["order"]["id"] == order_result["order"]["id"]
    assert any(order["id"] == order_result["order"]["id"] for order in orders_response.json())

    with SessionLocal() as db:
        assert db.scalar(select(Order).where(Order.customer_id == order_result["customer_id"]))


def test_operator_request_and_common_auto_responses() -> None:
    with TestClient(app) as client:
        operator_response = client.post(
            "/chat",
            json={"instagram_user_id": "pytest-operator-user", "message": "با اپراتور صحبت کنم"},
        )
        discount_response = client.post(
            "/chat",
            json={"instagram_user_id": "pytest-response-user", "message": "تخفیف دارید؟"},
        )
        thanks_response = client.post(
            "/chat",
            json={"instagram_user_id": "pytest-response-user", "message": "مرسی"},
        )

    assert "شماره موبایل" in operator_response.json()["reply"]
    assert "تخفیف" in discount_response.json()["reply"]
    assert "خواهش" in thanks_response.json()["reply"]


def test_finglish_price_order_faq_and_operator_flow() -> None:
    user_id = "pytest-finglish-user"
    with TestClient(app) as client:
        price_response = client.post(
            "/chat",
            json={
                "instagram_user_id": user_id,
                "message": "salam, gheymat iphone 15 chande?",
            },
        )
        phone_response = client.post(
            "/chat",
            json={
                "instagram_user_id": user_id,
                "message": "shomare man 09121234567 ast",
            },
        )
        order_response = client.post(
            "/chat",
            json={
                "instagram_user_id": user_id,
                "message": "haminja sefaresh mano sabt kon",
            },
        )
        shipping_response = client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "ersal be shahrestan darid?"},
        )
        discount_response = client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "takhfif darid?"},
        )
        operator_response = client.post(
            "/chat",
            json={"instagram_user_id": user_id, "message": "ba operator sohbat konam"},
        )

    assert price_response.json()["product"]["name"] == "Apple iPhone 15 128GB"
    assert phone_response.json()["phone_saved"] is True
    assert order_response.json()["order"]["product_name"] == "Apple iPhone 15 128GB"
    assert "ارسال آزمایشی" in shipping_response.json()["reply"]
    assert "تخفیف" in discount_response.json()["reply"]
    assert operator_response.json()["needs_human"] is True
