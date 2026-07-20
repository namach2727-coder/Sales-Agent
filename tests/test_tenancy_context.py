import json
import uuid
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.database import Base
from app.models import Store, StoreInstagramConnection
from app.tenancy import (
    AmbiguousTenantMappingError,
    InactiveTenantError,
    InvalidTenantHostError,
    SessionTenantResolutionUnavailableError,
    TenantActorType,
    TenantResolutionSource,
    UnknownConnectorAccountError,
    UnknownTenantError,
    UntrustedExplicitTenantError,
    normalize_correlation_id,
    resolve_explicit_internal_tenant,
    resolve_instagram_tenant,
    resolve_session_tenant,
    resolve_tenant_from_host,
    resolve_tenant_from_request,
    tenant_resolution_http_exception,
)


@pytest.fixture
def tenant_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        stores = {
            "default": Store(name="Default", slug="default", status="active"),
            "alpha": Store(name="Alpha", slug="alpha", status="active"),
            "disabled": Store(name="Disabled", slug="disabled-store", status="disabled"),
            "suspended": Store(
                name="Suspended", slug="suspended-store", status="suspended"
            ),
            "deleted": Store(name="Deleted", slug="deleted-store", status="deleted"),
        }
        db.add_all(stores.values())
        db.flush()
        db.add_all(
            [
                StoreInstagramConnection(
                    store_id=stores["alpha"].id,
                    ig_user_id="ig-alpha",
                    status="active",
                ),
                StoreInstagramConnection(
                    store_id=stores["default"].id,
                    ig_user_id="ig-inactive-connection",
                    status="inactive",
                ),
                StoreInstagramConnection(
                    store_id=stores["suspended"].id,
                    ig_user_id="ig-suspended-store",
                    status="active",
                ),
            ]
        )
        db.commit()
        yield db
    engine.dispose()


def settings(environment: str = "production") -> Settings:
    return Settings(
        app_env=environment,
        tenant_base_domain="agent.example.test",
        meta_ig_user_id="ig-development-default",
    )


def request_for(
    host: str,
    *,
    query: bytes = b"",
    body: bytes = b"",
    extra_headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    headers = [(b"host", host.encode("ascii"))]
    headers.extend(extra_headers or [])
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/resolve",
            "raw_path": b"/resolve",
            "query_string": query,
            "headers": headers,
            "client": ("127.0.0.1", 50000),
            "server": ("testserver", 443),
        },
        receive,
    )


def test_valid_tenant_subdomain(tenant_db) -> None:
    context = resolve_tenant_from_host(
        tenant_db, "alpha.agent.example.test", settings()
    )
    assert context.store_slug == "alpha"
    assert context.resolution_source is TenantResolutionSource.SUBDOMAIN
    assert context.is_default_fallback is False


def test_unknown_subdomain_fails_closed(tenant_db) -> None:
    with pytest.raises(UnknownTenantError):
        resolve_tenant_from_host(
            tenant_db, "missing.agent.example.test", settings()
        )


@pytest.mark.parametrize("host", ["", "not a host", "alpha.example.test/path", "bad\nhost"])
def test_malformed_host_fails_closed(tenant_db, host: str) -> None:
    with pytest.raises(InvalidTenantHostError):
        resolve_tenant_from_host(tenant_db, host, settings())


def test_localhost_in_development_is_marked_fallback(tenant_db) -> None:
    context = resolve_tenant_from_host(
        tenant_db, "127.0.0.1:8000", settings("development")
    )
    assert context.store_slug == "default"
    assert context.resolution_source is TenantResolutionSource.DEVELOPMENT_DEFAULT
    assert context.is_default_fallback is True


def test_localhost_in_production_fails_closed(tenant_db) -> None:
    with pytest.raises(InvalidTenantHostError):
        resolve_tenant_from_host(tenant_db, "localhost:8000", settings())


@pytest.mark.parametrize(
    "host",
    [
        "disabled-store.agent.example.test",
        "suspended-store.agent.example.test",
        "deleted-store.agent.example.test",
    ],
)
def test_inactive_store_host_fails_closed(tenant_db, host: str) -> None:
    with pytest.raises(InactiveTenantError):
        resolve_tenant_from_host(tenant_db, host, settings())


def test_known_active_instagram_account(tenant_db) -> None:
    context = resolve_instagram_tenant(tenant_db, "ig-alpha", settings())
    assert context.store_slug == "alpha"
    assert context.resolution_source is TenantResolutionSource.CONNECTOR
    assert context.actor.type is TenantActorType.CONNECTOR
    assert context.connector.account_id == "ig-alpha"
    assert context.connector.connection_id is not None


def test_unknown_instagram_account_fails_closed(tenant_db) -> None:
    with pytest.raises(UnknownConnectorAccountError):
        resolve_instagram_tenant(tenant_db, "ig-missing", settings())


def test_inactive_instagram_connection_fails_closed(tenant_db) -> None:
    with pytest.raises(UnknownConnectorAccountError):
        resolve_instagram_tenant(
            tenant_db, "ig-inactive-connection", settings("development"),
            allow_development_default_fallback=True,
        )


def test_inactive_connector_store_fails_closed(tenant_db) -> None:
    with pytest.raises(InactiveTenantError):
        resolve_instagram_tenant(tenant_db, "ig-suspended-store", settings())


def test_production_never_uses_global_instagram_fallback(tenant_db) -> None:
    with pytest.raises(UnknownConnectorAccountError):
        resolve_instagram_tenant(
            tenant_db,
            "ig-development-default",
            settings("production"),
            allow_development_default_fallback=True,
        )


def test_development_connector_fallback_must_be_explicit(tenant_db) -> None:
    development = settings("development")
    with pytest.raises(UnknownConnectorAccountError):
        resolve_instagram_tenant(
            tenant_db, "ig-development-default", development
        )
    context = resolve_instagram_tenant(
        tenant_db,
        "ig-development-default",
        development,
        allow_development_default_fallback=True,
    )
    assert context.store_slug == "default"
    assert context.resolution_source is TenantResolutionSource.DEVELOPMENT_DEFAULT
    assert context.is_default_fallback is True


def test_ambiguous_connector_mapping_fails_closed() -> None:
    store = SimpleNamespace(id=1, slug="alpha", status="active")
    connections = [
        SimpleNamespace(id=1, status="active", store=store),
        SimpleNamespace(id=2, status="active", store=store),
    ]

    class Results:
        def all(self):
            return connections

    class FakeSession:
        def scalars(self, _statement):
            return Results()

    with pytest.raises(AmbiguousTenantMappingError):
        resolve_instagram_tenant(FakeSession(), "duplicate", settings())


@pytest.mark.parametrize(
    ("query", "body", "headers"),
    [
        (b"store_slug=default", b"", []),
        (b"", json.dumps({"store_slug": "default"}).encode(), []),
        (b"", b"", [(b"x-store-slug", b"default"), (b"x-tenant-id", b"1")]),
    ],
)
def test_client_overrides_cannot_change_host_tenant(
    tenant_db, query: bytes, body: bytes, headers
) -> None:
    request = request_for(
        "alpha.agent.example.test",
        query=query,
        body=body,
        extra_headers=headers,
    )
    context = resolve_tenant_from_request(request, tenant_db, settings())
    assert context.store_slug == "alpha"


def test_correlation_id_preserved_from_defined_header(tenant_db) -> None:
    request = request_for(
        "alpha.agent.example.test",
        extra_headers=[(b"x-correlation-id", b"request-123")],
    )
    context = resolve_tenant_from_request(request, tenant_db, settings())
    assert context.correlation_id == "request-123"


@pytest.mark.parametrize("unsafe", ["line\nbreak", "line\rbreak", "x" * 129, "two spaces"])
def test_unsafe_correlation_id_is_replaced(unsafe: str) -> None:
    generated = normalize_correlation_id(unsafe)
    uuid.UUID(generated)
    assert generated != unsafe


def test_safe_serialization_has_no_credentials(tenant_db) -> None:
    configured = settings()
    configured.meta_access_token = "secret-access-token"
    context = resolve_instagram_tenant(tenant_db, "ig-alpha", configured)
    serialized = context.to_safe_dict()
    rendered = json.dumps(serialized)
    assert "secret-access-token" not in rendered
    assert "token" not in rendered.lower()
    assert serialized["connector"]["account_id"] == "ig-alpha"


def test_tenant_context_is_immutable(tenant_db) -> None:
    context = resolve_tenant_from_host(
        tenant_db, "alpha.agent.example.test", settings()
    )
    with pytest.raises(FrozenInstanceError):
        context.store_slug = "default"


def test_trusted_explicit_internal_resolution(tenant_db) -> None:
    context = resolve_explicit_internal_tenant(
        tenant_db,
        "alpha",
        trusted=True,
        actor_id="bootstrap-job",
        correlation_id="job-123",
    )
    assert context.store_slug == "alpha"
    assert context.resolution_source is TenantResolutionSource.EXPLICIT_INTERNAL
    assert context.actor.type is TenantActorType.SYSTEM
    assert context.actor.id == "bootstrap-job"
    assert context.correlation_id == "job-123"


def test_untrusted_explicit_resolution_fails(tenant_db) -> None:
    with pytest.raises(UntrustedExplicitTenantError):
        resolve_explicit_internal_tenant(tenant_db, "alpha", trusted=False)


def test_invalid_explicit_store_fails(tenant_db) -> None:
    with pytest.raises(UnknownTenantError):
        resolve_explicit_internal_tenant(
            tenant_db, "missing", trusted=True
        )


def test_inactive_explicit_store_fails(tenant_db) -> None:
    with pytest.raises(InactiveTenantError):
        resolve_explicit_internal_tenant(
            tenant_db, "suspended-store", trusted=True
        )


def test_session_resolution_is_explicitly_unavailable() -> None:
    with pytest.raises(SessionTenantResolutionUnavailableError) as caught:
        resolve_session_tenant()
    response = tenant_resolution_http_exception(caught.value)
    assert response.status_code == 503
