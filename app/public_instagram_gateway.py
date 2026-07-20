"""Public-only entry point for Meta's Instagram webhook.

Run this app behind the public HTTPS tunnel instead of exposing ``app.main``.
Only the Meta webhook, legal pages, and short-lived signed media downloads are
registered; the local setup, admin, catalog, sales, documentation, and static
routes do not exist on this app.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from app import models  # noqa: F401 - registers all database tables
from app.catalog_training import ensure_default_store
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.instagram import receive_instagram_webhook, verify_instagram_webhook
from app.legal import router as legal_router
from app.public_media import router as public_media_router
from app.module_catalog import ensure_default_instagram_connection, ensure_store_modules


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
SAFE_ACCESS_LOG = logging.getLogger("instagram_gateway.safe_access")
if not SAFE_ACCESS_LOG.handlers:
    handler = logging.FileHandler(
        LOG_DIR / "instagram_gateway_access.log", encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    SAFE_ACCESS_LOG.addHandler(handler)
    SAFE_ACCESS_LOG.setLevel(logging.INFO)
    SAFE_ACCESS_LOG.propagate = False


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create shared database tables when this entry point starts alone."""

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        store = ensure_default_store(db)
        ensure_store_modules(db, store, activate_legacy_defaults=True)
        ensure_default_instagram_connection(db, store, get_settings())
        db.commit()
    yield


app = FastAPI(
    title="Instagram Webhook Gateway",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
    redirect_slashes=False,
)


@app.middleware("http")
async def log_safe_access(request: Request, call_next):
    """Log only method, path, and status; never query strings or secrets."""
    response = await call_next(request)
    SAFE_ACCESS_LOG.info(
        "%s %s %s", request.method, request.url.path, response.status_code
    )
    return response

app.include_router(legal_router)
app.include_router(public_media_router)

app.add_api_route(
    "/webhooks/instagram",
    verify_instagram_webhook,
    methods=["GET"],
    response_class=PlainTextResponse,
    include_in_schema=False,
)
app.add_api_route(
    "/webhooks/instagram",
    receive_instagram_webhook,
    methods=["POST"],
    include_in_schema=False,
)
