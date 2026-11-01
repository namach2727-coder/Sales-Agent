"""Authenticated SEO onboarding API; no customer credentials in responses."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.config import Settings, get_settings
from app.database import get_db
from app.seo_growth.google_client import GoogleGscError
from app.seo_growth.security import SeoError, frontend_origin
from app.seo_growth.service import SeoOnboardingService, callback_service


router = APIRouter(tags=["seo-growth"])
PREFIX = "/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/seo"


class SiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connection_public_id: str = Field(min_length=36, max_length=36)
    property_id: str = Field(min_length=1, max_length=2048)


class DisconnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revoke_google: bool = False


def get_google_provider():
    """Test injection boundary; production creates a Google-only client lazily."""
    return None


def service(tenant_public_id: str, store_public_id: str, request: Request,
            response: Response, db: Session = Depends(get_db),
            settings: Settings = Depends(get_settings),
            principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
            provider=Depends(get_google_provider)) -> SeoOnboardingService:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    mutation = request.method == "POST"
    try:
        if mutation:
            # Custom header + exact Origin. Never trust forwarded Host/Origin
            # to choose the OAuth destination or to authorize a mutation.
            if request.headers.get("x-csrf-token") != "seo" or request.headers.get("origin") != frontend_origin(settings, require_callback=False):
                raise SeoError("seo_csrf_invalid", 403)
        return SeoOnboardingService(db, settings, principal, tenant_public_id, store_public_id,
            mutation=mutation, cleanup=request.url.path.endswith("/disconnect"), provider=provider)
    except SeoError as exc:
        fail(exc)


def fail(error: Exception):
    status = error.status if isinstance(error, SeoError) else 502
    code = error.code
    messages = {
        "seo_access_required": "دسترسی سرویس سئو برای این حساب فعال نیست.",
        "seo_not_enabled": "سرویس سئو هنوز فعال نشده است.",
        "seo_pilot_admin_required": "مدیریت دسترسی آزمایشی فقط برای مدیر سیستم مجاز است.",
        "seo_pilot_revision_conflict": "دسترسی هم‌زمان تغییر کرده است؛ وضعیت تازه را دریافت کنید و دوباره بررسی کنید.",
        "seo_pilot_limit_below_usage": "سقف انتخابی کمتر از تعداد سایت‌ها یا اتصال‌های موجود است.",
        "seo_scope_inactive": "حساب یا فضای کاری فعال نیست.",
        "seo_configuration_required": "اتصال Google هنوز آماده نشده است.",
        "seo_property_not_granted": "این سایت در فهرست دسترسی Google شما نیست.",
        "seo_connect_rate_limited": "چند دقیقه دیگر برای اتصال دوباره تلاش کنید.",
        "seo_google_consent_required": "اتصال را دوباره شروع کنید و مجوز Google را تأیید کنید.",
        "seo_site_limit": "ظرفیت سایت‌های این حساب تکمیل است.",
        "seo_connection_limit": "ظرفیت اتصال‌های Google این حساب تکمیل است.",
        "seo_reauthorization_required": "برای ادامه، Google را دوباره متصل کنید.",
        "google_authorization_expired": "مجوز Google معتبر نیست؛ دوباره متصل شوید.",
        "google_rate_limited": "محدودیت موقت Google؛ کمی بعد دوباره تلاش کنید.",
    }
    raise HTTPException(status_code=status, detail={"code": code,
        "message": messages.get(code, "درخواست انجام نشد؛ وضعیت اتصال را بررسی کنید.")},
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@router.get(PREFIX + "/status")
def status(svc: SeoOnboardingService = Depends(service)):
    return svc.status()


@router.post(PREFIX + "/google/connect")
def connect(svc: SeoOnboardingService = Depends(service)):
    try:
        return svc.begin()
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.get("/api/v1/seo/google/callback", include_in_schema=False)
def callback(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
             principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
             provider=Depends(get_google_provider)):
    query = request.query_params
    # Remove auth query values before application-server access logging. The
    # deployment gate also requires proxy/platform auth-route log redaction.
    request.scope["query_string"] = b""
    headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
    try:
        if any(len(query.getlist(k)) > 1 for k in ("state", "code", "error")):
            raise SeoError("seo_oauth_state_invalid")
        state, code, error = query.get("state", ""), query.get("code"), query.get("error")
        if (code and error) or (code and len(code) > 4096):
            raise SeoError("seo_oauth_state_invalid")
        svc = callback_service(db, settings, principal, state, provider)
        try:
            outcome = svc.complete(state, code=code, denied=bool(error))
        except (SeoError, GoogleGscError):
            db.rollback()
            outcome = "failed"
        return RedirectResponse(svc.redirect(outcome), status_code=303, headers=headers)
    except SeoError as exc:
        fail(exc)


@router.get(PREFIX + "/google/{connection_public_id}/properties")
def properties(connection_public_id: str, svc: SeoOnboardingService = Depends(service)):
    try:
        return {"items": [{"property_id": p.site_url, "permission_level": p.permission_level}
                          for p in svc.properties(connection_public_id)]}
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.post(PREFIX + "/sites", status_code=201)
def add_site(payload: SiteCreate, svc: SeoOnboardingService = Depends(service)):
    try:
        return site_read(svc.add_site(payload.connection_public_id, payload.property_id))
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.get(PREFIX + "/sites")
def sites(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10000),
          svc: SeoOnboardingService = Depends(service)):
    try:
        return {"items": [site_read(s) for s in svc.sites(limit=limit, offset=offset)]}
    except SeoError as exc:
        fail(exc)


@router.post(PREFIX + "/sites/{site_public_id}/disconnect")
def disconnect_site(site_public_id: str, svc: SeoOnboardingService = Depends(service)):
    try:
        svc.disconnect_site(site_public_id)
        return {"status": "disconnected"}
    except SeoError as exc:
        fail(exc)


@router.post(PREFIX + "/google/{connection_public_id}/disconnect")
def disconnect(connection_public_id: str, payload: DisconnectRequest,
               svc: SeoOnboardingService = Depends(service)):
    try:
        return svc.disconnect(connection_public_id, revoke_google=payload.revoke_google)
    except SeoError as exc:
        fail(exc)


def site_read(site) -> dict:
    return {"public_id": site.public_id, "property_id": site.property_id,
            "permission_level": site.permission_level, "status": site.status,
            "created_at": site.created_at, "updated_at": site.updated_at,
            "sync_status": "not_started"}
