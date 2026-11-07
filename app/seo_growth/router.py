"""Authenticated SEO onboarding API; no customer credentials in responses."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
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
CALLBACK_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


class SeoOAuthCallbackRoute(APIRoute):
    def get_route_handler(self):
        handle = super().get_route_handler()

        async def private_callback(request: Request) -> Response:
            # Parse into this Request before clearing the raw ASGI query.
            # Authentication can reject the callback before the endpoint runs.
            _ = request.query_params
            request.scope["query_string"] = b""
            try:
                response = await handle(request)
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), **CALLBACK_HEADERS}
                raise
            response.headers.update(CALLBACK_HEADERS)
            return response

        return private_callback


class SiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connection_public_id: str = Field(min_length=36, max_length=36)
    property_id: str = Field(min_length=1, max_length=2048)


class DisconnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revoke_google: bool = False


class AnalysisPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date


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
        "seo_analysis_not_enabled": "گزارش آزمایشی سئو هنوز فعال نشده است.",
        "seo_sync_not_enabled": "همگام‌سازی داده‌های سئو هنوز فعال نشده است.",
        "seo_sync_invalid_window": "بازه زمانی انتخاب‌شده معتبر نیست.",
        "seo_sync_window_too_large": "بازه هر درخواست همگام‌سازی حداکثر ۹۰ روز است.",
        "seo_sync_data_not_final": "داده‌های این بازه هنوز نهایی نشده‌اند.",
        "seo_sync_already_running": "همگام‌سازی این سایت در حال اجراست.",
        "seo_sync_lease_lost": "مالکیت عملیات همگام‌سازی تغییر کرده است؛ دوباره وضعیت را بررسی کنید.",
        "seo_sync_failed": "همگام‌سازی کامل نشد؛ کمی بعد دوباره تلاش کنید.",
        "seo_analysis_rate_limited": "سقف درخواست گزارش پر شده است؛ حداقل یک دقیقه فاصله و حداکثر ۱۲ درخواست در ۲۴ ساعت مجاز است.",
        "seo_site_not_connected": "ابتدا سایت را دوباره متصل کنید.",
        "seo_connection_changed": "وضعیت اتصال تغییر کرده است؛ وضعیت تازه را دریافت کنید.",
        "google_invalid_response": "داده معتبر برای گزارش دریافت نشد؛ کمی بعد دوباره بررسی کنید.",
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


def callback(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
             principal: AuthenticatedPrincipal = Depends(require_authenticated_principal),
             provider=Depends(get_google_provider)):
    query = request.query_params
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
        return RedirectResponse(svc.redirect(outcome), status_code=303)
    except SeoError as exc:
        fail(exc)


router.add_api_route("/api/v1/seo/google/callback", callback, methods=["GET"],
    include_in_schema=False, route_class_override=SeoOAuthCallbackRoute)


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
        site = svc.add_site(payload.connection_public_id, payload.property_id)
        return site_read(site, own_connection_id=site.connection_id)
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.get(PREFIX + "/sites")
def sites(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10000),
          svc: SeoOnboardingService = Depends(service)):
    try:
        connection = svc.db.scalar(svc._connections())
        return {"items": [site_read(s, own_connection_id=connection.id if connection else None)
                          for s in svc.sites(limit=limit, offset=offset)]}
    except SeoError as exc:
        fail(exc)


@router.post(PREFIX + "/sites/{site_public_id}/analysis-preview")
def analyze(site_public_id: str, payload: AnalysisPreviewRequest,
            svc: SeoOnboardingService = Depends(service)):
    from app.seo_growth.reporting import analysis_preview
    try:
        return analysis_preview(svc, site_public_id)
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.get(PREFIX + "/sites/{site_public_id}/sync-runs")
def sync_runs(site_public_id: str, limit: int = Query(20, ge=1, le=100),
              offset: int = Query(0, ge=0, le=10000),
              svc: SeoOnboardingService = Depends(service)):
    from app.seo_growth.persisted_reporting import sync_history
    try:
        return sync_history(svc, site_public_id, limit=limit, offset=offset)
    except SeoError as exc:
        fail(exc)


@router.get(PREFIX + "/sites/{site_public_id}/analysis")
def persisted_analyze(site_public_id: str, svc: SeoOnboardingService = Depends(service)):
    from app.seo_growth.persisted_reporting import persisted_analysis
    try:
        return persisted_analysis(svc, site_public_id)
    except (SeoError, GoogleGscError) as exc:
        fail(exc)


@router.post(PREFIX + "/sites/{site_public_id}/sync")
def sync(site_public_id: str, payload: SyncRequest, svc: SeoOnboardingService = Depends(service)):
    from app.seo_growth.sync import sync_site
    try:
        return sync_site(svc, site_public_id, payload.start_date, payload.end_date)
    except (SeoError, GoogleGscError) as exc:
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


def site_read(site, *, own_connection_id: int | None = None) -> dict:
    return {"public_id": site.public_id, "property_id": site.property_id,
            "permission_level": site.permission_level, "status": site.status,
            "created_at": site.created_at, "updated_at": site.updated_at,
            "sync_status": "not_started",
            "analysis_available": site.status == "connected" and site.connection_id == own_connection_id}
