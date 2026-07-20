import pytest
from sqlalchemy import delete, select

from app.database import Base, SessionLocal, engine
from app.models import (
    Conversation,
    Customer,
    InstagramCommentEvent,
    InstagramCommentPublicReply,
    InstagramEvent,
    InstagramMediaProduct,
    ManyChatEvent,
    Order,
    TelegramEvent,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    Base.metadata.create_all(bind=engine)


def remove_pytest_customers() -> None:
    with SessionLocal() as db:
        db.execute(
            delete(InstagramCommentPublicReply).where(
                InstagramCommentPublicReply.comment_id.like("pytest-%")
            )
        )
        db.execute(
            delete(InstagramCommentEvent).where(
                InstagramCommentEvent.comment_id.like("pytest-%")
            )
        )
        db.execute(
            delete(InstagramMediaProduct).where(
                InstagramMediaProduct.media_id.like("pytest-%")
            )
        )
        db.execute(
            delete(InstagramEvent).where(InstagramEvent.sender_id.like("pytest-%"))
        )
        db.execute(
            delete(InstagramEvent).where(InstagramEvent.message_id.like("pytest-%"))
        )
        db.execute(
            delete(TelegramEvent).where(TelegramEvent.sender_id.like("pytest-%"))
        )
        db.execute(
            delete(ManyChatEvent).where(ManyChatEvent.contact_id.like("pytest-%"))
        )
        customer_ids = list(
            db.scalars(
                select(Customer.id).where(
                    Customer.instagram_user_id.like("pytest-%")
                    | Customer.instagram_user_id.like("telegram:pytest-%")
                    | Customer.instagram_user_id.like("manychat:pytest-%")
                )
            ).all()
        )
        if customer_ids:
            db.execute(delete(Order).where(Order.customer_id.in_(customer_ids)))
            db.execute(delete(Conversation).where(Conversation.customer_id.in_(customer_ids)))
            db.execute(delete(Customer).where(Customer.id.in_(customer_ids)))
        db.commit()


@pytest.fixture(autouse=True)
def clean_test_customers():
    remove_pytest_customers()
    yield
    remove_pytest_customers()
