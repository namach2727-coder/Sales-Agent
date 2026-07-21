from sqlalchemy import create_engine
from collections.abc import Generator
from threading import Lock

from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_demo_bootstrap_lock = Lock()


class Base(DeclarativeBase):
    pass


def SessionLocal() -> Session:
    """Create an application session with legacy non-production demo data."""

    db = _SessionFactory()
    if settings.app_env.strip().casefold() in {"development", "demo", "test"}:
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
