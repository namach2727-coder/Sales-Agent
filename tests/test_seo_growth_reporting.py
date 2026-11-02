"""Offline report arithmetic, provider boundaries and current-access regression."""
from datetime import UTC, date, datetime, timedelta
import json

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Store, TenantAuditLog, TenantMembership, UserIdentity
from app.seo_growth import reporting
from app.seo_growth.google_client import GoogleGscError
from app.seo_growth.models import SeoAccessGrant, SeoGoogleConnection, SeoSite
from app.seo_growth.reporting import preview_from_google
from app.seo_growth.service import SeoOnboardingService
from test_seo_growth_onboarding import api, connected, env, prefix


HEADERS = {"Origin": "https://customer.example", "X-CSRF-Token": "seo"}


def daily_rows(start, end):
    return [{"keys": [(start + timedelta(days=i)).isoformat()],
             "clicks": 1.0 if i < 28 else 2.0, "impressions": 10.0 if i < 28 else 20.0,
             "position": 5.0 if i < 28 else 10.0, "ctr": 0.99}
            for i in range((end - start).days + 1)]


def query_rows():
    return [{"keys": ["synthetic query", "https://example.com/page"], "clicks": 1.0,
             "impressions": 200.0, "position": 12.0}]


def pure_preview(daily=None, queries=None):
    end = date(2026, 10, 29)
    return preview_from_google(property_id="sc-domain:example.com",
        daily_body={"rows": daily if daily is not None else daily_rows(end - timedelta(days=55), end)},
        query_body={"rows": queries if queries is not None else query_rows()},
        end_date=end, generated_at=datetime(2026, 11, 2, tzinfo=UTC))


def test_preview_uses_date_totals_and_weighted_positions_not_query_totals_or_provider_ctr():
    result = pure_preview()
    assert result["current"]["clicks"] == 56 and result["current"]["impressions"] == 560
    assert result["previous"]["clicks"] == 28 and result["previous"]["impressions"] == 280
    assert result["current"]["ctr"] == 0.1 and result["current"]["position"] == 10
    assert result["comparison"]["clicks_change_percent"] == 100
    assert result["comparison"]["ctr_change_percentage_points"] == 0
    assert result["comparison"]["position_change"] == 5
    assert result["opportunities"][0]["action_mode"] == "proposal_only"
    assert result["source"] == "google_search_console" and result["persistence"] == "response_only"
    assert result["query_sample"]["coverage"] == "google_top_rows_not_exhaustive"


def test_missing_daily_rows_are_null_and_disable_percentage_comparison():
    rows = daily_rows(date(2026, 9, 4), date(2026, 10, 29))
    rows.pop()
    result = pure_preview(daily=rows)
    assert result["current"]["observed_days"] == 27
    assert result["current"]["missing_dates"] == ["2026-10-29"]
    assert result["current"]["daily"][-1]["clicks"] is None
    assert result["comparison"]["status"] == "incomplete_coverage"
    assert all(value is None for key, value in result["comparison"].items() if key != "status")


def test_empty_and_observed_zero_are_distinct_with_undefined_ctr_and_position():
    empty = pure_preview(daily=[], queries=[])
    assert empty["current"]["clicks"] is None and len(empty["current"]["missing_dates"]) == 28
    rows = daily_rows(date(2026, 9, 4), date(2026, 10, 29))
    for row in rows:
        row.update(clicks=0, impressions=0, position=0)
    zero = pure_preview(daily=rows, queries=[])
    assert zero["current"]["clicks"] == 0 and zero["current"]["impressions"] == 0
    assert zero["current"]["ctr"] is None and zero["current"]["position"] is None
    assert zero["comparison"]["clicks_change_percent"] is None


@pytest.mark.parametrize("change", [
    {"clicks": True}, {"clicks": 1.5}, {"clicks": -1}, {"clicks": 100},
    {"impressions": float("inf")}, {"position": float("nan")}, {"position": True},
    {"keys": ["2026-10-30"]}, {"keys": ["20261029"]}, {"keys": []},
])
def test_malformed_google_metrics_are_rejected_without_fabricating_data(change):
    rows = daily_rows(date(2026, 9, 4), date(2026, 10, 29))
    rows[0].update(change)
    with pytest.raises(GoogleGscError, match="google_invalid_response"):
        pure_preview(daily=rows)


@pytest.mark.parametrize("page", ["javascript:alert(1)", "https://example.com.evil.invalid/a", "https://user:secret@example.com/a", "https://example.com:bad/a"])
def test_opportunity_page_must_belong_to_the_google_property(page):
    rows = query_rows(); rows[0]["keys"][1] = page
    with pytest.raises(GoogleGscError, match="google_invalid_response"):
        pure_preview(queries=rows)


def test_duplicate_rows_and_query_caps_fail_closed_and_sample_limit_is_disclosed():
    rows = daily_rows(date(2026, 9, 4), date(2026, 10, 29)); rows[1] = rows[0]
    with pytest.raises(GoogleGscError): pure_preview(daily=rows)
    with pytest.raises(GoogleGscError): pure_preview(queries=query_rows() * 2)
    queries = [{**query_rows()[0], "keys": [f"synthetic {i}", f"https://example.com/{i}"]} for i in range(500)]
    result = pure_preview(queries=queries)
    assert result["query_sample"]["limit_reached"] is True
    assert len(result["opportunities"]) == 20
    with pytest.raises(GoogleGscError): pure_preview(queries=queries + query_rows())


@pytest.fixture()
def report_env(env):
    env["settings"].seo_analysis_preview_enabled = True
    connection = connected(env)
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    calls = []
    def analytics(**kwargs):
        calls.append(kwargs)
        if env.get("report_hook"):
            env["report_hook"]()
        if env.get("report_failure"):
            raise GoogleGscError(env["report_failure"])
        return {"rows": daily_rows(kwargs["start_date"], kwargs["end_date"]) if kwargs["dimensions"] == ("date",) else query_rows()}
    env["fake"].search_analytics = analytics
    env.update(site=site, connection=connection, report_calls=calls)
    return env


def endpoint(env):
    return prefix(env) + f'/sites/{env["site"].public_id}/analysis-preview'


def test_api_returns_bounded_final_web_preview_and_audits_no_metrics_or_credentials(report_env, api):
    env = report_env
    response = api.post(endpoint(env), headers=HEADERS, json={})
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["data_state"] == "final" and body["search_type"] == "web"
    assert [c["dimensions"] for c in env["report_calls"]] == [("date",), ("query", "page")]
    assert [c["row_limit"] for c in env["report_calls"]] == [56, 500]
    assert env["report_calls"][0]["property_id"] == "sc-domain:example.com"
    audits = list(env["db"].scalars(select(TenantAuditLog).where(TenantAuditLog.action.like("seo.analysis_preview_%"))))
    assert [a.action for a in audits] == ["seo.analysis_preview_started", "seo.analysis_preview_completed"]
    audit_json = json.dumps([a.details_json for a in audits])
    assert "synthetic query" not in audit_json and all(a.details_json == {} for a in audits)
    assert all(secret not in response.text + audit_json for secret in [env["fake"].access, env["fake"].refresh, env["principal"].session_id])
    assert api.get(prefix(env) + "/sites").json()["items"][0]["analysis_available"] is True


def test_report_window_uses_pacific_date_not_server_or_browser_date(report_env, api, monkeypatch):
    monkeypatch.setattr(reporting, "_clock", lambda: datetime(2026, 11, 2, 0, 30, tzinfo=UTC))
    response = api.post(endpoint(report_env), headers=HEADERS, json={})
    assert response.status_code == 200
    assert response.json()["current"]["end_date"] == "2026-10-29"
    assert response.json()["previous"]["end_date"] == "2026-10-01"


def test_pacific_calendar_is_available_without_system_timezone_files():
    import zoneinfo
    original = zoneinfo.TZPATH
    try:
        zoneinfo.reset_tzpath(())
        zoneinfo.ZoneInfo.clear_cache()
        pacific = datetime(2026, 11, 2, 0, 30, tzinfo=UTC).astimezone(zoneinfo.ZoneInfo("America/Los_Angeles"))
        assert pacific.date() == date(2026, 11, 1)
        assert pacific.utcoffset() == timedelta(hours=-8)
    finally:
        zoneinfo.reset_tzpath(original)
        zoneinfo.ZoneInfo.clear_cache()


def test_preview_requires_its_own_flag_grant_and_explicit_csrf(report_env, api):
    env = report_env
    assert api.post(endpoint(env), json={}).status_code == 403
    env["settings"].seo_analysis_preview_enabled = False
    assert api.post(endpoint(env), headers=HEADERS, json={}).status_code == 403
    env["settings"].seo_analysis_preview_enabled = True
    env["grant"].status = "disabled";env["db"].commit()
    assert api.post(endpoint(env), headers=HEADERS, json={}).status_code == 403
    assert env["report_calls"] == []


def test_dates_and_filters_cannot_be_supplied_by_client(report_env, api):
    assert api.post(endpoint(report_env), headers=HEADERS, json={"start_date": "2020-01-01"}).status_code == 422
    assert report_env["report_calls"] == []


def test_storewide_cooldown_and_daily_budget_are_consumed_before_provider_call(report_env, api):
    env = report_env
    env["report_failure"] = "google_network_unavailable"
    assert api.post(endpoint(env), headers=HEADERS, json={}).status_code == 502
    assert api.post(endpoint(env), headers=HEADERS, json={}).status_code == 429
    assert len(env["report_calls"]) == 1
    started = env["db"].scalar(select(TenantAuditLog).where(TenantAuditLog.action == "seo.analysis_preview_started"))
    started.created_at = datetime.now(UTC) - timedelta(hours=2)
    for _ in range(11):
        env["db"].add(TenantAuditLog(tenant_id=env["tenant"].id, store_id=env["store"].id,
            actor_identity_id=env["user"].id, action="seo.analysis_preview_started", target_type="seo",
            target_public_id=env["site"].public_id, details_json={}, created_at=datetime.now(UTC)-timedelta(hours=2)))
    env["db"].commit()
    assert api.post(endpoint(env), headers=HEADERS, json={}).status_code == 429


def test_foreign_scope_and_colleague_google_connection_cannot_be_used(report_env, api):
    env = report_env
    foreign = Store(tenant_id=env["tenant"].id, name="Other", slug="other", status="active")
    env["db"].add(foreign);env["db"].commit()
    env["db"].add(SeoAccessGrant(tenant_id=env["tenant"].id, store_id=foreign.id,
        max_sites=1, max_connections=1, expires_at=datetime.now(UTC)+timedelta(days=1)))
    env["db"].commit()
    assert api.post(endpoint(env).replace(env["store"].public_id,foreign.public_id), headers=HEADERS,json={}).status_code == 404
    other = UserIdentity(email="other@example.invalid",normalized_email="other@example.invalid",display_name="Other")
    env["db"].add(other);env["db"].flush();env["connection"].user_id=other.id;env["db"].commit()
    assert api.post(endpoint(env),headers=HEADERS,json={}).status_code==404
    assert api.get(prefix(env)+"/sites").json()["items"][0]["analysis_available"] is False
    assert env["report_calls"] == []


@pytest.mark.parametrize("change,expected", [("grant",403),("connection",409),("membership",404),("site",409),("flag",403)])
def test_inflight_change_cannot_return_a_report_from_stale_access(report_env,api,change,expected):
    env=report_env
    def revoke():
        if env.get("changed"):return
        env["changed"]=True
        if change=="flag":env["settings"].seo_analysis_preview_enabled=False;return
        with Session(env["engine"]) as other:
            if change=="grant":other.get(SeoAccessGrant,env["grant"].id).status="disabled"
            if change=="connection":other.get(SeoGoogleConnection,env["connection"].id).status="disconnected"
            if change=="membership":other.get(TenantMembership,env["membership"].id).status="revoked"
            if change=="site":other.get(SeoSite,env["site"].id).status="disconnected"
            other.commit()
    env["report_hook"]=revoke
    response=api.post(endpoint(env),headers=HEADERS,json={})
    assert response.status_code==expected and "synthetic query" not in response.text
    assert env["db"].scalar(select(func.count()).select_from(TenantAuditLog).where(TenantAuditLog.action=="seo.analysis_preview_completed"))==0


@pytest.mark.parametrize("code,expected_status", [("google_authorization_expired","reauthorization_required"),("google_access_denied_or_quota","connected")])
def test_only_explicit_authorization_expiry_marks_connection_for_reauthorization(report_env,api,code,expected_status):
    env=report_env;env["report_failure"]=code
    assert api.post(endpoint(env),headers=HEADERS,json={}).status_code==502
    env["db"].refresh(env["connection"])
    assert env["connection"].status==expected_status


def test_current_google_property_permission_is_rechecked_before_analytics(report_env,api):
    report_env["fake"].entries=[]
    assert api.post(endpoint(report_env),headers=HEADERS,json={}).status_code==403
    assert report_env["report_calls"]==[]


def test_aggregation_mismatch_and_unsafe_aggregate_counts_are_rejected():
    end=date(2026,10,29)
    with pytest.raises(GoogleGscError):
        preview_from_google(property_id="sc-domain:example.com",end_date=end,generated_at=datetime.now(UTC),
            daily_body={"responseAggregationType":"byPage","rows":[]},query_body={"rows":[]})
    rows=daily_rows(date(2026,9,4),end)
    for row in rows:row["impressions"]=2**53-1
    with pytest.raises(GoogleGscError):pure_preview(daily=rows)


def test_expired_old_credential_does_not_revoke_a_concurrent_new_connection(report_env,api):
    env=report_env
    def reconnect():
        if env.get("changed"):return
        env["changed"]=True
        new_ciphertext=env["svc"]()._seal("new-synthetic-token","refresh")
        with Session(env["engine"]) as other:
            conn=other.get(SeoGoogleConnection,env["connection"].id)
            conn.encrypted_refresh_token=new_ciphertext
            other.commit()
    env["report_hook"]=reconnect;env["report_failure"]="google_authorization_expired"
    assert api.post(endpoint(env),headers=HEADERS,json={}).status_code==502
    env["db"].refresh(env["connection"])
    assert env["connection"].status=="connected"


def test_revocation_while_waiting_for_store_lock_prevents_even_a_google_call(report_env, api, monkeypatch):
    env=report_env
    original=SeoOnboardingService._lock
    def raced_lock(service):
        with Session(env["engine"]) as other:
            other.get(TenantMembership,env["membership"].id).status="revoked"
            other.commit()
        original(service)
    monkeypatch.setattr(SeoOnboardingService,"_lock",raced_lock)
    assert api.post(endpoint(env),headers=HEADERS,json={}).status_code==404
    assert env["report_calls"]==[]
