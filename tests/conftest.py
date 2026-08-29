import os

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError


POSTGRES_TEST_URL_VARIABLE = "DIRECTPILOT_POSTGRES_TEST_URL"
ALEMBIC_HEAD = "0014_transport_neutral_inbound"


def configure_explicit_postgres_test_database() -> bool:
    """Opt in to PostgreSQL tests without accepting a normal application URL."""

    explicit_url = os.environ.get(POSTGRES_TEST_URL_VARIABLE, "").strip()
    configured_url = os.environ.get("DATABASE_URL", "").strip()
    if not explicit_url:
        if configured_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise RuntimeError(
                "PostgreSQL pytest runs require "
                f"{POSTGRES_TEST_URL_VARIABLE}; DATABASE_URL alone is rejected"
            )
        return False

    parsed = make_url(explicit_url)
    if parsed.get_backend_name() != "postgresql":
        raise RuntimeError(
            f"{POSTGRES_TEST_URL_VARIABLE} must use PostgreSQL"
        )
    if not parsed.username or not parsed.password or not parsed.host:
        raise RuntimeError(
            f"{POSTGRES_TEST_URL_VARIABLE} must include credentials and host"
        )
    database_name = (parsed.database or "").casefold()
    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"{POSTGRES_TEST_URL_VARIABLE} database name must end with _test"
        )

    os.environ["DATABASE_URL"] = explicit_url
    os.environ["APP_ENV"] = "test"
    return True


POSTGRES_TEST_ENABLED = configure_explicit_postgres_test_database()

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

# ``app.database`` has now constructed and cached the explicitly opted-in
# PostgreSQL engine. Do not leak that override into tests which instantiate a
# fresh ``Settings`` object to validate deployment defaults.
if POSTGRES_TEST_ENABLED:
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    if POSTGRES_TEST_ENABLED:
        try:
            with engine.connect() as connection:
                revision = connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                )
        except SQLAlchemyError as exc:
            raise RuntimeError(
                "PostgreSQL test database is unavailable or has not been "
                "migrated; run `python -m alembic upgrade head` first"
            ) from exc
        if revision != ALEMBIC_HEAD:
            raise RuntimeError(
                "PostgreSQL test database must be migrated to "
                f"{ALEMBIC_HEAD} before pytest; found {revision!r}"
            )
        return
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
