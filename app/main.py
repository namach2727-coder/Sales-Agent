from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.chat import order_to_dict, process_chat
from app.admin import router as admin_router
from app.admin_content import router as admin_content_router
from app.admin_modules import router as admin_modules_router
from app.catalog_runtime import list_products as list_catalog_products
from app.config import get_settings
from app.database import Base, engine, get_db
from app.instagram import router as instagram_router
from app.instagram_setup import router as instagram_setup_router
from app.legal import router as legal_router
from app.manychat import router as manychat_router
from app.public_media import router as public_media_router
from app.telegram import router as telegram_router
from app.telegram_setup import router as telegram_setup_router
from app import models  # noqa: F401 - registers database models
from app.models import Customer, FAQ, Order, Product
from app.schemas import ChatRequest, ChatResponse, FAQRead, LeadRead, OrderRead, ProductRead

settings = get_settings()
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.9.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(admin_router)
app.include_router(admin_content_router)
app.include_router(admin_modules_router)
app.include_router(instagram_router)
app.include_router(instagram_setup_router)
app.include_router(legal_router)
app.include_router(manychat_router)
app.include_router(public_media_router)
app.include_router(telegram_router)
app.include_router(telegram_setup_router)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/demo")


@app.get("/demo", include_in_schema=False)
def demo() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


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
