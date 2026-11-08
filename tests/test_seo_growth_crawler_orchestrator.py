from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.seo_growth.crawl_leases import CrawlLeaseGrant
from app.seo_growth.crawler_orchestrator import (
    CrawlOrchestrationError,
    run_crawl_preview,
)
from app.seo_growth.models import SeoGoogleConnection, SeoSite


class _Session:
    def __init__(self, site, connection):
        self.site = site
        self.connection = connection
        self.commits = 0
        self.rollbacks = 0

    def get(self, model, identity):
        if model is SeoSite and identity == self.site.id:
            return self.site
        if model is SeoGoogleConnection and identity == self.connection.id:
            return self.connection
        return None

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _scope(property_id="sc-domain:example.com"):
    site = SimpleNamespace(
        id=33, tenant_id=11, store_id=22, connection_id=44,
        property_id=property_id, status="connected",
    )
    connection = SimpleNamespace(
        id=44, tenant_id=11, store_id=22, status="connected",
    )
    return site, connection


def _grant(host="blog.example.com"):
    return CrawlLeaseGrant(
        host=host,
        crawl_id=str(uuid4()),
        lease_token="a" * 64,
        expires_at=datetime(2026, 11, 8, 12, 0, tzinfo=UTC),
    )


def test_orchestrator_checks_consent_scope_renews_lease_and_persists_audit(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)
    grant = _grant()
    calls = {"acquire": [], "renew": [], "release": [], "audit": [], "preview": []}

    def acquire(_db, **kwargs):
        calls["acquire"].append(kwargs)
        return grant

    def renew(_db, current, **kwargs):
        calls["renew"].append((current, kwargs))
        return current

    def release(_db, current):
        calls["release"].append(current)
        return True

    def audit(_db, **kwargs):
        calls["audit"].append(kwargs)

    def preview(seed, **kwargs):
        calls["preview"].append((seed, kwargs))
        kwargs["before_page"](seed, 0)
        kwargs["audit_callback"](
            event_kind="page", outcome="fetched", raw_url=seed,
            robots_decision="allow", http_status=200,
            bytes_received=10, duration_ms=5, error_code=None,
        )
        return {"coverage_status": "complete", "pages_crawled": 1}

    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.acquire_crawl_lease", acquire)
    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.renew_crawl_lease", renew)
    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.release_crawl_lease", release)
    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.record_crawl_audit_event", audit)
    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.crawl_preview", preview)

    result = run_crawl_preview(
        db, tenant_id=11, store_id=22, site_id=33,
        seed_url="https://blog.example.com/start",
        consent_check=lambda: True, retention_days=30,
        resolver=lambda _host, _port: ["93.184.216.34"],
    )

    assert result == {
        "crawl_id": grant.crawl_id, "coverage_status": "complete", "pages_crawled": 1,
    }
    assert calls["acquire"][0]["host"] == "blog.example.com"
    assert calls["preview"][0][1]["allowed_path_prefix"] == "/"
    assert len(calls["renew"]) == 1
    assert calls["release"] == [grant]
    assert calls["audit"][0]["retention_days"] == 30
    assert calls["audit"][0]["crawl_id"] == grant.crawl_id
    assert db.commits >= 3


def test_orchestrator_enforces_url_prefix_property_scope(monkeypatch):
    site, connection = _scope("https://www.example.com/blog/")
    db = _Session(site, connection)
    grant = _grant("www.example.com")
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease",
        lambda _db, **_kwargs: grant,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.renew_crawl_lease",
        lambda _db, current, **_kwargs: current,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.release_crawl_lease",
        lambda _db, _current: True,
    )
    seen = {}

    def preview(seed, **kwargs):
        seen["seed"] = seed
        seen["prefix"] = kwargs["allowed_path_prefix"]
        return {"coverage_status": "complete"}

    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.crawl_preview", preview)
    result = run_crawl_preview(
        db, tenant_id=11, store_id=22, site_id=33,
        seed_url="https://www.example.com/blog/article",
        consent_check=lambda: True, retention_days=30,
        resolver=lambda _host, _port: ["93.184.216.34"],
    )
    assert result["coverage_status"] == "complete"
    assert seen == {
        "seed": "https://www.example.com/blog/article",
        "prefix": "/blog/",
    }


def test_orchestrator_rejects_missing_consent_before_claiming_lease(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)

    def unexpected_claim(*_args, **_kwargs):
        raise AssertionError("lease must not be acquired without consent")

    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease", unexpected_claim,
    )
    with pytest.raises(CrawlOrchestrationError, match="seo_crawler_consent_required"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://example.com/",
            consent_check=lambda: False, retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )


def test_orchestrator_rejects_seed_outside_verified_property_before_claiming_lease(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)

    def unexpected_claim(*_args, **_kwargs):
        raise AssertionError("lease must not be acquired for an out-of-scope seed")

    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease", unexpected_claim,
    )
    with pytest.raises(CrawlOrchestrationError, match="seo_crawler_site_scope_mismatch"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://evil.example.net/",
            consent_check=lambda: True, retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )


def test_orchestrator_releases_lease_when_crawl_fails(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)
    grant = _grant()
    released = []
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease",
        lambda _db, **_kwargs: grant,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.release_crawl_lease",
        lambda _db, current: released.append(current) or True,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.crawl_preview",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("test failure")),
    )

    with pytest.raises(RuntimeError, match="test failure"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://blog.example.com/",
            consent_check=lambda: True, retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )
    assert released == [grant]
    assert db.rollbacks >= 1


def test_orchestrator_rechecks_revocable_consent_before_each_page(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)
    grant = _grant()
    consent_states = iter([True, False])
    released = []
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease",
        lambda _db, **_kwargs: grant,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.release_crawl_lease",
        lambda _db, current: released.append(current) or True,
    )

    def preview(seed, **kwargs):
        kwargs["before_page"](seed, 0)
        return {"coverage_status": "complete"}

    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.crawl_preview", preview)
    with pytest.raises(CrawlOrchestrationError, match="seo_crawler_consent_revoked"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://blog.example.com/",
            consent_check=lambda: next(consent_states), retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )
    assert released == [grant]



def test_orchestrator_rechecks_consent_before_each_http_request(monkeypatch):
    site, connection = _scope()
    db = _Session(site, connection)
    grant = _grant()
    consent_states = iter([True, False])
    released = []
    transport_calls = []

    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease",
        lambda _db, **_kwargs: grant,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.release_crawl_lease",
        lambda _db, current: released.append(current) or True,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator._request_once",
        lambda *args, **kwargs: transport_calls.append((args, kwargs)),
    )

    def preview(seed, **kwargs):
        kwargs["request_once"](
            SimpleNamespace(url=seed), "93.184.216.34",
            timeout=1.0, max_body_bytes=100,
        )
        return {"coverage_status": "complete"}

    monkeypatch.setattr("app.seo_growth.crawler_orchestrator.crawl_preview", preview)
    with pytest.raises(CrawlOrchestrationError, match="seo_crawler_consent_revoked"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://blog.example.com/",
            consent_check=lambda: next(consent_states), retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )

    assert transport_calls == []
    assert released == [grant]



def test_orchestrator_rolls_back_when_initial_lease_commit_fails(monkeypatch):
    site, connection = _scope()

    class _FailFirstCommitSession(_Session):
        def commit(self):
            self.commits += 1
            if self.commits == 1:
                raise RuntimeError("commit failed")

    db = _FailFirstCommitSession(site, connection)
    grant = _grant()
    released = []
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease",
        lambda _db, **_kwargs: grant,
    )
    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.release_crawl_lease",
        lambda _db, current: released.append(current) or True,
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url="https://blog.example.com/",
            consent_check=lambda: True, retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )

    assert db.rollbacks == 1
    assert released == []



@pytest.mark.parametrize(
    "property_id,seed_url",
    [
        ("https://www.example.com/blog/?token=secret", "https://www.example.com/blog/article"),
        ("sc-domain:example.com:8443", "https://example.com:8443/"),
    ],
)
def test_orchestrator_rejects_noncanonical_gsc_property_identifiers(
    monkeypatch, property_id, seed_url,
):
    site, connection = _scope(property_id)
    db = _Session(site, connection)

    def unexpected_claim(*_args, **_kwargs):
        raise AssertionError("invalid property identifiers must not claim a lease")

    monkeypatch.setattr(
        "app.seo_growth.crawler_orchestrator.acquire_crawl_lease", unexpected_claim,
    )
    with pytest.raises(CrawlOrchestrationError, match="seo_crawler_invalid_site_property"):
        run_crawl_preview(
            db, tenant_id=11, store_id=22, site_id=33,
            seed_url=seed_url,
            consent_check=lambda: True, retention_days=30,
            resolver=lambda _host, _port: ["93.184.216.34"],
        )
