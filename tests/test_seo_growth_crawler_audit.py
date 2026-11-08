from uuid import uuid4

import pytest

from app import models  # noqa: F401 - register shared model metadata
from app.database import Base
from app.seo_growth.crawler_audit import (
    record_crawl_audit_event,
    url_audit_identity,
)


class _Session:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)


def test_crawl_audit_metadata_is_tenant_site_scoped_and_expiring():
    table = Base.metadata.tables["seo_crawl_audit_events"]
    foreign_keys = [
        tuple(element.parent.name for element in constraint.elements)
        for constraint in table.foreign_key_constraints
    ]
    assert ("site_id", "tenant_id", "store_id") in foreign_keys
    assert {"crawl_id", "event_kind", "outcome", "robots_decision",
            "url_host", "url_fingerprint", "http_status", "bytes_received",
            "duration_ms", "error_code", "created_at", "expires_at"} <= set(table.c.keys())
    assert not {"url", "raw_url", "query_string", "headers", "response_body"} & set(table.c.keys())


def test_url_audit_identity_excludes_query_and_fragment_secrets():
    first = url_audit_identity("https://example.com/private/page?access_token=secret#section")
    second = url_audit_identity("https://example.com/private/page?access_token=other")
    assert first == second
    assert first[0] == "example.com"
    assert "secret" not in first[1]


def test_record_crawl_audit_event_stages_sanitized_expiring_evidence():
    db = _Session()
    event = record_crawl_audit_event(
        db,
        tenant_id=11,
        store_id=22,
        site_id=33,
        crawl_id=str(uuid4()),
        event_kind="page",
        outcome="fetched",
        raw_url="https://example.com/products/item?session=private",
        http_status=200,
        bytes_received=512,
        duration_ms=37,
        retention_days=90,
    )
    assert db.added == [event]
    assert event.url_host == "example.com"
    assert event.url_fingerprint
    assert event.bytes_received == 512
    assert event.expires_at > event.created_at
    assert not hasattr(event, "raw_url")


@pytest.mark.parametrize("kwargs", [
    {"tenant_id": 0},
    {"event_kind": "headers"},
    {"outcome": "success"},
    {"robots_decision": "unknown"},
    {"http_status": 700},
    {"bytes_received": -1},
    {"duration_ms": -1},
    {"retention_days": 0},
    {"error_code": "secret token"},
])
def test_record_crawl_audit_event_rejects_invalid_values(kwargs):
    values = {
        "tenant_id": 11,
        "store_id": 22,
        "site_id": 33,
        "crawl_id": str(uuid4()),
        "event_kind": "page",
        "outcome": "fetched",
        "raw_url": "https://example.com/page",
        "retention_days": 90,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        record_crawl_audit_event(_Session(), **values)
