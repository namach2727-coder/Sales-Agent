import ipaddress
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.admin_schemas import AgentTestInput, CatalogTrainingInput
from app.catalog_training import (
    CatalogPublishError,
    create_training_draft,
    get_admin_state,
    publish_training_draft,
    serialize_draft,
    update_training_draft,
)
from app.chat import process_chat
from app.config import Settings, get_settings
from app.database import get_db
from app.schemas import ChatRequest


router = APIRouter(tags=["admin-console"])
STATIC_DIR = Path(__file__).resolve().parent / "static"
LOCAL_HOSTNAMES = {"127.0.0.1", "localhost", "::1"}


def require_local_admin(request: Request, settings: Settings) -> None:
    if settings.app_env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    client_host = request.client.host if request.client else ""
    try:
        is_loopback = ipaddress.ip_address(client_host).is_loopback
    except ValueError:
        is_loopback = client_host == "testclient"
    if not is_loopback:
        raise HTTPException(status_code=403, detail="Admin console is local-only")
    if request.url.hostname not in LOCAL_HOSTNAMES:
        raise HTTPException(status_code=403, detail="Invalid local admin host")


def require_admin_read(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    require_local_admin(request, settings)


def require_admin_mutation(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    require_local_admin(request, settings)
    host = request.headers.get("host", "")
    expected_origin = f"{request.url.scheme}://{host}".rstrip("/")
    supplied_origin = request.headers.get("origin", "").rstrip("/")
    if not supplied_origin or supplied_origin != expected_origin:
        raise HTTPException(status_code=403, detail="Invalid admin request origin")
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site and fetch_site not in {"same-origin", "none"}:
        raise HTTPException(status_code=403, detail="Cross-site admin request blocked")


@router.get("/admin", include_in_schema=False, dependencies=[Depends(require_admin_read)])
def admin_page() -> FileResponse:
    response = FileResponse(STATIC_DIR / "admin.html")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'none'; form-action 'self'"
    )
    return response


@router.get("/admin/api/state", dependencies=[Depends(require_admin_read)])
def admin_state(db: Session = Depends(get_db)) -> dict[str, object]:
    return get_admin_state(db)


@router.post("/admin/api/drafts/analyze", dependencies=[Depends(require_admin_mutation)])
def analyze_draft(
    payload: CatalogTrainingInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    draft, warnings = create_training_draft(db, payload.model_dump(mode="json"))
    return {"draft": serialize_draft(draft), "warnings": warnings}


@router.put("/admin/api/drafts/{draft_id}", dependencies=[Depends(require_admin_mutation)])
def update_draft(
    draft_id: int,
    payload: CatalogTrainingInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        draft, warnings = update_training_draft(
            db, draft_id, payload.model_dump(mode="json")
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CatalogPublishError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"draft": serialize_draft(draft), "warnings": warnings}


@router.post(
    "/admin/api/drafts/{draft_id}/publish",
    dependencies=[Depends(require_admin_mutation)],
)
def publish_draft(
    draft_id: int,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        publish_training_draft(db, draft_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CatalogPublishError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return get_admin_state(db)


@router.post("/admin/api/test", dependencies=[Depends(require_admin_mutation)])
def test_agent(
    payload: AgentTestInput,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = process_chat(
        db,
        ChatRequest(
            instagram_user_id=f"admin-preview:{uuid.uuid4().hex}",
            message=payload.message,
            customer_name="پیش‌نمایش مدیر",
        ),
        channel="admin-test",
        commit=False,
    )
    product = result.get("product")
    response = {
        "reply": result["reply"],
        "product": (
            {"id": product.id, "name": product.name, "price": product.price}
            if product is not None
            else None
        ),
        "needs_human": result["needs_human"],
    }
    db.rollback()
    return response

