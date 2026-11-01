"""Offline F1 security and API regression; no Google or customer DB calls."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
import secrets
from urllib.parse import parse_qs, urlsplit

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal
from app.authentication.dependencies import require_authenticated_principal
from app.config import Settings, get_settings
from app.database import Base, get_db
from app.models import Store, TenantAuditLog, UserIdentity
from app.seo_growth.google_client import GSC_READONLY_SCOPE, GoogleGscError, GoogleGscProperty, GoogleOAuthTokens, GoogleSearchConsoleClient
from app.seo_growth.models import SeoAccessGrant, SeoGoogleConnection, SeoOAuthAttempt, SeoSite
from app.seo_growth.router import get_google_provider, router
from app.seo_growth.security import SeoCipher, SeoError, digest
from app.seo_growth.service import SeoOnboardingService, callback_service
from app.tenant_management.service import TenantStoreService
from tools.seeding import SeedRunner, default_registry


class GoogleDouble:
    def __init__(self, settings):
        self.client = GoogleSearchConsoleClient(client_id="synthetic-client", client_secret=secrets.token_urlsafe(), redirect_uri=settings.seo_google_redirect_uri)
        self.refresh = secrets.token_urlsafe()
        self.access = secrets.token_urlsafe()
        self.entries = [GoogleGscProperty("sc-domain:example.com", "siteOwner"), GoogleGscProperty("https://example.org/", "siteFullUser")]
        self.exchange_calls = 0
        self.hook = None
        self.failure = None
        self.revoked = False

    def authorization_url(self, **kwargs):
        return self.client.authorization_url(**kwargs)

    def exchange_code(self, **kwargs):
        self.exchange_calls += 1
        if self.hook:
            self.hook()
        if self.failure:
            raise GoogleGscError(self.failure)
        return GoogleOAuthTokens(self.access, 3600, self.refresh, GSC_READONLY_SCOPE)

    def refresh_access_token(self, **kwargs):
        if self.failure:
            raise GoogleGscError(self.failure)
        return GoogleOAuthTokens(self.access, 3600, None, GSC_READONLY_SCOPE)

    def list_properties(self, **kwargs):
        return self.entries

    def revoke_token(self, **kwargs):
        return self.revoked


@pytest.fixture()
def env(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seo.db'}", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    SeedRunner(engine, default_registry()).run("production")
    db = Session(engine, expire_on_commit=False)
    user = UserIdentity(email="seo@example.invalid", normalized_email="seo@example.invalid", display_name="SEO Test", email_verified=True)
    db.add(user); db.commit()
    tenant, store, membership = TenantStoreService(db, actor_identity_id=user.id).bootstrap(
        tenant_name="SEO Customer", tenant_slug="seo-customer", store_name="SEO Workspace", store_slug="seo-workspace", owner_identity=user)
    principal = AuthenticatedPrincipal(user_id=user.id, email=user.email, display_name=user.display_name,
        session_id=secrets.token_urlsafe(), authenticated_at=datetime.now(UTC), platform_role_codes=(), tenant_memberships=())
    settings = Settings(_env_file=None, app_env="test", seo_growth_enabled=True,
        seo_google_redirect_uri="https://customer.example/api/v1/seo/google/callback",
        seo_frontend_origin="https://customer.example", seo_google_client_id="synthetic-client",
        seo_google_client_secret=secrets.token_urlsafe(), seo_token_encryption_key=Fernet.generate_key().decode())
    grant = SeoAccessGrant(tenant_id=tenant.id, store_id=store.id, max_sites=1, max_connections=1,
        expires_at=datetime.now(UTC) + timedelta(days=7))
    db.add(grant); db.commit()
    fake = GoogleDouble(settings)
    def svc(**kwargs):
        return SeoOnboardingService(db, settings, kwargs.pop("principal", principal), tenant.public_id, kwargs.pop("store_public_id", store.public_id), mutation=True, provider=fake, **kwargs)
    yield {"db": db, "engine": engine, "user": user, "tenant": tenant, "store": store,
        "principal": principal, "settings": settings, "grant": grant, "fake": fake, "svc": svc, "membership": membership}
    db.close(); engine.dispose()


def start(env):
    result = env["svc"]().begin()
    return parse_qs(urlsplit(result["authorization_url"]).query)["state"][0]


def connected(env):
    state = start(env)
    assert env["svc"]().complete(state, code=secrets.token_urlsafe()) == "connected"
    return env["db"].scalar(select(SeoGoogleConnection))


def test_state_pkce_and_refresh_never_persist_as_plaintext(env):
    state = start(env)
    attempt = env["db"].scalar(select(SeoOAuthAttempt))
    assert attempt.state_digest == digest(state) and state not in attempt.encrypted_verifier
    assert attempt.session_digest == digest(env["principal"].session_id)
    assert env["svc"]().complete(state, code=secrets.token_urlsafe()) == "connected"
    connection = env["db"].scalar(select(SeoGoogleConnection))
    assert env["fake"].refresh not in connection.encrypted_refresh_token
    assert env["svc"]()._open(connection.encrypted_refresh_token, "refresh") == env["fake"].refresh
    assert env["db"].get(SeoOAuthAttempt, attempt.id).encrypted_verifier is None
    audits = json.dumps([r.details_json for r in env["db"].scalars(select(TenantAuditLog))])
    assert all(s not in audits for s in [state, env["fake"].access, env["fake"].refresh])


@pytest.mark.parametrize("change", ["disabled", "no_grant", "expired"])
def test_independent_access_fails_closed(env, change):
    if change == "disabled": env["settings"].seo_growth_enabled = False
    elif change == "no_grant": env["grant"].status = "disabled"
    else: env["grant"].expires_at = datetime.now(UTC) - timedelta(seconds=1)
    env["db"].commit()
    with pytest.raises(SeoError): env["svc"]().begin()
    assert env["fake"].exchange_calls == 0


@pytest.mark.parametrize("change", ["session", "user", "state", "expired"])
def test_callback_binding_and_expiry(env, change):
    state = start(env)
    principal = env["principal"]
    if change == "session": principal = replace(principal, session_id=secrets.token_urlsafe())
    if change == "user": principal = replace(principal, user_id=principal.user_id + 99)
    if change == "state": state = secrets.token_urlsafe()
    if change == "expired":
        env["db"].scalar(select(SeoOAuthAttempt)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
        env["db"].commit()
    with pytest.raises(SeoError, match="seo_oauth_state_invalid"):
        callback_service(env["db"], env["settings"], principal, state, env["fake"])
    assert env["fake"].exchange_calls == 0


def test_successful_and_failed_exchange_cannot_be_replayed(env):
    state = start(env)
    env["fake"].failure = "google_network_unavailable"
    with pytest.raises(GoogleGscError): env["svc"]().complete(state, code="synthetic-code")
    env["fake"].failure = None
    with pytest.raises(SeoError): env["svc"]().complete(state, code="synthetic-code")
    assert env["fake"].exchange_calls == 1
    connected(env)
    last = env["db"].scalars(select(SeoOAuthAttempt).order_by(SeoOAuthAttempt.id.desc())).first()
    assert last.used_at is not None


def test_state_is_durably_claimed_before_exchange(env):
    state = start(env)
    def replay():
        with Session(env["engine"]) as other:
            with pytest.raises(SeoError, match="seo_oauth_state_invalid"):
                callback_service(other, env["settings"], env["principal"], state, env["fake"])
    env["fake"].hook = replay
    env["svc"]().complete(state, code="synthetic-code")


def test_denial_consumes_state_without_provider_exchange(env):
    state = start(env)
    assert env["svc"]().complete(state, code=None, denied=True) == "denied"
    with pytest.raises(SeoError): env["svc"]().complete(state, code="synthetic-code")
    assert env["fake"].exchange_calls == 0


def test_missing_refresh_token_cannot_reuse_previous_google_account(env):
    connection = connected(env)
    old = connection.encrypted_refresh_token
    env["fake"].refresh = None
    state = start(env)
    with pytest.raises(SeoError, match="seo_google_consent_required"):
        env["svc"]().complete(state, code="synthetic-code")
    assert connection.encrypted_refresh_token == old


def test_later_connect_invalidates_inflight_callback(env):
    state = start(env)
    env["fake"].hook = lambda: start(env)
    with pytest.raises(SeoError, match="seo_oauth_state_invalid"):
        env["svc"]().complete(state, code="synthetic-code")
    assert env["db"].scalar(select(SeoGoogleConnection)) is None


def test_connect_rate_limit_survives_restart_attempts(env):
    for _ in range(5): start(env)
    with pytest.raises(SeoError, match="seo_connect_rate_limited"): start(env)


def test_site_must_be_google_granted_and_quota_is_independent(env):
    connection = connected(env)
    with pytest.raises(SeoError, match="seo_property_not_granted"):
        env["svc"]().add_site(connection.public_id, "sc-domain:attacker.example")
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    assert env["svc"]().add_site(connection.public_id, site.property_id).public_id == site.public_id
    with pytest.raises(SeoError, match="seo_site_limit"):
        env["svc"]().add_site(connection.public_id, "https://example.org/")


def test_cross_store_or_user_connection_is_non_disclosing(env):
    connection = connected(env)
    other = Store(tenant_id=env["tenant"].id, name="Other Workspace", slug="other-workspace", status="active")
    env["db"].add(other); env["db"].flush()
    env["db"].add(SeoAccessGrant(tenant_id=env["tenant"].id, store_id=other.id,
        expires_at=datetime.now(UTC) + timedelta(days=1)))
    env["db"].commit()
    with pytest.raises(SeoError, match="not_found"):
        env["svc"](store_public_id=other.public_id).properties(connection.public_id)
    another = replace(env["principal"], user_id=env["user"].id + 999)
    with pytest.raises(SeoError, match="not_found"):
        env["svc"](principal=another).properties(connection.public_id)


def test_disabled_membership_cannot_read_existing_connection(env):
    connected(env)
    env["membership"].status = "disabled"; env["db"].commit()
    with pytest.raises(SeoError, match="not_found"): env["svc"]().sites()


def test_cipher_cannot_be_swapped_between_scopes_or_purposes(env):
    cipher = SeoCipher(env["settings"])
    value = cipher.encrypt(secrets.token_urlsafe(), tenant=1, store=2, user=3, purpose="refresh")
    for args in [(2, 2, 3, "refresh"), (1, 3, 3, "refresh"), (1, 2, 4, "refresh"), (1, 2, 3, "pkce")]:
        with pytest.raises(SeoError, match="seo_credential_unavailable"):
            cipher.decrypt(value, tenant=args[0], store=args[1], user=args[2], purpose=args[3])


def test_reconnect_never_silently_reattaches_old_sites(env):
    connection = connected(env)
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    connected(env)
    env["db"].refresh(site)
    assert site.status == "disconnected"
    env["svc"]().add_site(connection.public_id, site.property_id)
    assert site.status == "connected"


@pytest.mark.parametrize("failure,expected", [("google_authorization_expired", "reauthorization_required"), ("google_network_unavailable", "connected")])
def test_revoked_permission_is_distinct_from_transient_error(env, failure, expected):
    connection = connected(env)
    env["fake"].failure = failure
    with pytest.raises(GoogleGscError): env["svc"]().properties(connection.public_id)
    env["db"].refresh(connection)
    assert connection.status == expected


@pytest.mark.parametrize("revoked", [False, True])
def test_disconnect_erases_token_and_honestly_reports_revocation(env, revoked):
    connection = connected(env)
    site = env["svc"]().add_site(connection.public_id, "sc-domain:example.com")
    state = start(env)
    env["grant"].status = "disabled"; env["db"].commit()
    env["fake"].revoked = revoked
    result = env["svc"](cleanup=True).disconnect(connection.public_id, revoke_google=True)
    assert result["google_revocation"] == ("revoked" if revoked else "unconfirmed")
    assert connection.encrypted_refresh_token is None
    env["db"].refresh(site)
    assert site.status == "disconnected"
    with pytest.raises(SeoError): callback_service(env["db"], env["settings"], env["principal"], state)


@pytest.fixture()
def api(env):
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_db] = lambda: env["db"]
    app.dependency_overrides[get_settings] = lambda: env["settings"]
    app.dependency_overrides[require_authenticated_principal] = lambda: env["principal"]
    app.dependency_overrides[get_google_provider] = lambda: env["fake"]
    with TestClient(app, base_url="https://customer.example") as client:
        yield client


def prefix(env):
    return f'/api/v1/tenants/{env["tenant"].public_id}/stores/{env["store"].public_id}/seo'


@pytest.mark.parametrize("headers", [{}, {"Origin": "https://evil.example", "X-CSRF-Token": "seo"}, {"Origin": "https://customer.example"}])
def test_api_csrf_rejects_untrusted_requests(env, api, headers):
    assert api.post(prefix(env) + "/google/connect", headers=headers).status_code == 403
    assert env["db"].scalar(select(SeoOAuthAttempt)) is None


def test_api_full_onboarding_and_disconnect_returns_no_credentials(env, api):
    headers = {"Origin": "https://customer.example", "X-CSRF-Token": "seo"}
    response = api.post(prefix(env) + "/google/connect", headers=headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    state = parse_qs(urlsplit(response.json()["authorization_url"]).query)["state"][0]
    code = secrets.token_urlsafe()
    response = api.get("/api/v1/seo/google/callback", params={"state": state, "code": code}, follow_redirects=False)
    assert response.status_code == 303 and "seo=connected" in response.headers["location"]
    assert code not in response.headers["location"] and state not in response.headers["location"]
    connection = api.get(prefix(env) + "/status").json()["connection"]
    props = api.get(prefix(env) + f'/google/{connection["public_id"]}/properties')
    assert props.json()["items"][0]["property_id"] == "sc-domain:example.com"
    response = api.post(prefix(env) + "/sites", headers=headers,
        json={"connection_public_id": connection["public_id"], "property_id": "sc-domain:example.com"})
    assert response.status_code == 201
    assert response.json()["sync_status"] == "not_started"
    for secret in [env["fake"].access, env["fake"].refresh]:
        assert secret not in props.text + response.text + json.dumps(connection)
    assert api.get(prefix(env) + "/sites").json()["items"][0]["public_id"] == response.json()["public_id"]
    assert api.get("/api/v1/seo/google/callback", params={"state": state, "code": code}, follow_redirects=False).status_code == 400
    assert api.post(prefix(env) + f'/google/{connection["public_id"]}/disconnect', headers=headers, json={}).json()["status"] == "disconnected"


def test_api_foreign_tenant_does_not_disclose_sites(env, api):
    connected(env)
    response = api.get(prefix(env).replace(env["tenant"].public_id, "00000000-0000-0000-0000-000000000000") + "/sites")
    assert response.status_code == 404


def test_local_disconnect_still_works_when_oauth_configuration_is_removed(env, api):
    connection = connected(env)
    env["settings"].seo_google_redirect_uri = ""
    env["settings"].seo_token_encryption_key = ""
    response = api.post(prefix(env) + f"/google/{connection.public_id}/disconnect",
        headers={"Origin": "https://customer.example", "X-CSRF-Token": "seo"}, json={})
    assert response.status_code == 200
    env["db"].refresh(connection)
    assert connection.encrypted_refresh_token is None


def test_callback_rejects_duplicate_parameters_without_reflecting_code(env, api):
    state = start(env)
    secret = secrets.token_urlsafe()
    response = api.get("/api/v1/seo/google/callback", params=[("state", state), ("code", secret), ("code", secret)], follow_redirects=False)
    assert response.status_code == 400 and secret not in response.text
    assert env["fake"].exchange_calls == 0


def test_api_requires_authentication(env):
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_db] = lambda: env["db"]
    app.dependency_overrides[get_settings] = lambda: env["settings"]
    with TestClient(app) as client:
        assert client.get(prefix(env) + "/status").status_code == 401
