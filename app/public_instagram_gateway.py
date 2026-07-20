"""Public-only entry point for Meta's Instagram webhook.

Run this app behind the public HTTPS tunnel instead of exposing ``app.main``.
Only the Meta webhook, legal pages, and short-lived signed media downloads are
registered; the local setup, admin, catalog, sales, documentation, and static
routes do not exist on this app.
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from threading import RLock

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from app import models  # noqa: F401 - registers all database tables
from app.database import Base, engine
from app.instagram import receive_instagram_webhook, verify_instagram_webhook
from app.legal import router as legal_router
from app.public_media import router as public_media_router


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
SAFE_ACCESS_LOG_PATH = LOG_DIR / "instagram_gateway_access.log"
_SAFE_ACCESS_LOG_LOCK = RLock()


def configure_safe_access_logger() -> tuple[logging.Logger, logging.FileHandler]:
    """Return the process-wide safe access logger in a usable state.

    The function is idempotent and intentionally owns only the file handler for
    this log.  It neither clears nor replaces handlers installed by the host
    process.  Re-enabling the named logger also makes startup deterministic when
    third-party code has configured logging before this app is created.
    """

    with _SAFE_ACCESS_LOG_LOCK:
        LOG_DIR.mkdir(exist_ok=True)
        logger = logging.getLogger("instagram_gateway.safe_access")
        expected_path = SAFE_ACCESS_LOG_PATH.resolve()
        handler = next(
            (
                candidate
                for candidate in logger.handlers
                if isinstance(candidate, logging.FileHandler)
                and Path(candidate.baseFilename).resolve() == expected_path
            ),
            None,
        )
        if handler is None:
            handler = logging.FileHandler(SAFE_ACCESS_LOG_PATH, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            logger.addHandler(handler)

        logger.disabled = False
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger, handler


SAFE_ACCESS_LOG, _ = configure_safe_access_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create shared database tables when this entry point starts alone."""

    configure_safe_access_logger()
    Base.metadata.create_all(bind=engine)
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
    logger, handler = configure_safe_access_logger()
    with _SAFE_ACCESS_LOG_LOCK:
        logger.info("%s %s %s", request.method, request.url.path, response.status_code)
        handler.flush()
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
