from __future__ import annotations

from collections.abc import Generator
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings, get_settings


def build_engine(settings: Settings) -> Engine:
    is_sqlite = settings.database_url.startswith("sqlite")
    options: dict[str, object] = {"pool_pre_ping": True}
    if is_sqlite:
        options["connect_args"] = {"check_same_thread": False}
    else:
        options.update(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            connect_args={"connect_timeout": settings.database_connect_timeout},
        )
    return create_engine(settings.database_url, **options)


settings = get_settings()
engine = build_engine(settings)
_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_demo_bootstrap_lock = Lock()


class Base(DeclarativeBase):
    pass


def check_database_connection(target: Engine = engine) -> None:
    with target.connect() as connection:
        connection.execute(text("SELECT 1"))


def SessionLocal() -> Session:
    """Create an application session with legacy non-production demo data."""

    db = _SessionFactory()
    if settings.app_env in {"development", "demo", "test"}:
        from app.seed import bootstrap_development_demo_data

        try:
            with _demo_bootstrap_lock:
                bootstrap_development_demo_data(db)
        except Exception:
            db.close()
            raise
    return db


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
