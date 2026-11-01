from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.chat import order_to_dict, process_chat
from app.admin import router as admin_router
from app.admin_content import router as admin_content_router
from app.admin_modules import router as admin_modules_router
from app.catalog_runtime import list_products as list_catalog_products
from app.catalog.router import router as business_catalog_router
from app.business_knowledge.router import router as business_knowledge_router
from app.automation.router import router as automation_router
from app.automation_rules.router import router as automation_rules_router
from app.ai_assistant.router import router as ai_assistant_router
from app.seo_growth.router import router as seo_growth_router
from app.seo_growth.admin_router import router as seo_pilot_admin_router
from app.commerce.router import router as commerce_router
from app.commerce.service import manual_payment_runtime_summary
from app.conversation_core.router import router as conversation_core_router
from app.config import (get_settings, llm_provider_readiness, llm_runtime_summary, payexa_runtime_summary, validate_runtime_settings)
from app.database import Base, SessionLocal, check_database_connection, engine, get_db
from app.instagram import router as instagram_router
from app.instagram_channel.router import (
    public_router as instagram_channel_public_router,
    router as instagram_channel_router,
)
from app.instagram_onboarding.router import router as instagram_onboarding_router
from app.instagram_setup import router as instagram_setup_router
from app.legal import router as legal_router
from app.manychat import router as manychat_router
from app.public_media import router as public_media_router
from app.telegram import router as telegram_router
from app.telegram_setup import router as telegram_setup_router
from app.tenant_management.router import router as tenant_management_router
from app.authentication.router import router as authentication_router
from app import models  # noqa: F401 - registers database models
from app.models import Customer, FAQ, Order, Product
from app.observability import (
    CorrelationIdMiddleware,
    SecurityHeadersMiddleware,
    configure_logging,
)
from app.operations import readiness, require_database_at_head
from app.schemas import ChatRequest, ChatResponse, FAQRead, LeadRead, OrderRead, ProductRead

settings = get_settings()
STATIC_DIR = Path(__file__).parent / "static"
DEPLOYED_AT_BOOT = settings.deployed
configure_logging(settings)
logger = logging.getLogger("sales_assistant.lifecycle")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if DEPLOYED_AT_BOOT:
        validate_runtime_settings(settings)
        llm_provider, llm_model, llm_credential_configured = (
            llm_runtime_summary(settings)
        )
        logger.info(
            "llm runtime configuration provider=%s model=%s credential_configured=%s",
            llm_provider,
            llm_model,
            str(llm_credential_configured).lower(),
            extra={"event_code": "llm.runtime_config"},
        )
        openai_ready, groq_credential_ready, groq_model_ready = (
            llm_provider_readiness(settings)
        )
        logger.info(
            "llm provider readiness openai_credential=%s groq_credential=%s groq_model=%s",
            str(openai_ready).lower(),
            str(groq_credential_ready).lower(),
            str(groq_model_ready).lower(),
            extra={"event_code": "llm.provider_readiness"},
        )
        payexa_base_url, payexa_callback_base_url, payexa_credential_configured = (
            payexa_runtime_summary(settings)
        )
        logger.info(
            "payexa runtime configuration base_url=%s callback_base_url=%s credential_configured=%s",
            payexa_base_url or "-",
            payexa_callback_base_url or "-",
            str(payexa_credential_configured).lower(),
            extra={"event_code": "payment.payexa_runtime_config"},
        )
    logger.info("application starting", extra={"event_code": "application.starting"})
    if DEPLOYED_AT_BOOT:
        try:
            check_database_connection(engine)
            require_database_at_head(engine)
            with SessionLocal() as payment_runtime_db:
                active_cards, active_default_cards = manual_payment_runtime_summary(
                    payment_runtime_db
                )
            logger.info(
                "manual payment readiness active_cards=%s active_default_cards=%s",
                active_cards,
                active_default_cards,
                extra={"event_code": "payment.manual_runtime_config"},
            )
        except Exception as exc:
            logger.error(
                "deployment database validation failed",
                extra={"event_code": "database.startup_validation_failed"},
            )
            raise RuntimeError("deployment database validation failed") from exc
    else:
        Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()
        logger.info("application stopped", extra={"event_code": "application.stopped"})


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
if settings.security_headers_enabled:
    app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Authorization", "X-Request-ID", "X-CSRF-Token"],
    )
if settings.force_https:
    app.add_middleware(HTTPSRedirectMiddleware)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(admin_router)
app.include_router(admin_content_router)
app.include_router(admin_modules_router)
app.include_router(instagram_router)
app.include_router(instagram_channel_public_router)
app.include_router(instagram_channel_router)
app.include_router(instagram_onboarding_router)
app.include_router(instagram_setup_router)
app.include_router(legal_router)
app.include_router(manychat_router)
app.include_router(public_media_router)
app.include_router(telegram_router)
app.include_router(telegram_setup_router)
app.include_router(authentication_router)
app.include_router(tenant_management_router)
app.include_router(business_catalog_router)
app.include_router(business_knowledge_router)
app.include_router(conversation_core_router)
app.include_router(automation_router)
app.include_router(automation_rules_router)
app.include_router(ai_assistant_router)
app.include_router(seo_growth_router)
app.include_router(seo_pilot_admin_router)
app.include_router(commerce_router)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/demo")


@app.get("/demo", include_in_schema=False)
def demo() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@app.get("/live", tags=["system"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/ready", tags=["system"])
def readiness_check():
    result = readiness(engine)
    payload = {
        "status": "ready" if result.ready else "not_ready",
        "database": result.database,
        "migration": result.migration,
    }
    return payload if result.ready else JSONResponse(status_code=503, content=payload)


@app.get("/version", tags=["system"])
def version() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "build": settings.build_sha,
        "environment": settings.app_env,
    }


@app.get("/products", response_model=list[ProductRead], tags=["catalog"])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    _, products = list_catalog_products(db)
    return products


@app.get("/faqs", response_model=list[FAQRead], tags=["catalog"])
def list_faqs(db: Session = Depends(get_db)) -> list[FAQ]:
    return list(db.scalars(select(FAQ).where(FAQ.is_active.is_(True)).order_by(FAQ.id)).all())


@app.get("/leads", response_model=list[LeadRead], tags=["sales-assistant"])
def list_leads(db: Session = Depends(get_db)) -> list[Customer]:
    return list(
        db.scalars(
            select(Customer)
            .where(Customer.phone.is_not(None))
            .order_by(Customer.created_at.desc())
        ).all()
    )


@app.get("/orders", response_model=list[OrderRead], tags=["sales-assistant"])
def list_orders(db: Session = Depends(get_db)) -> list[dict]:
    orders = db.scalars(
        select(Order)
        .options(joinedload(Order.customer), joinedload(Order.product))
        .order_by(Order.created_at.desc())
    ).all()
    return [order_to_dict(order) for order in orders]


@app.post("/chat", response_model=ChatResponse, tags=["sales-assistant"])
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> dict:
    return process_chat(db, payload, channel="web")
