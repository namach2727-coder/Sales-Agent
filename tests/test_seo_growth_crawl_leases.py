from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import UniqueConstraint

from app import models  # noqa: F401 - register shared model metadata
from app.database import Base
from app.seo_growth.crawl_leases import (
    CrawlLeaseError,
    acquire_crawl_lease,
    release_crawl_lease,
    renew_crawl_lease,
)


class _Session:
    def __init__(self, values):
        self.values = list(values)
        self.added = []
        self.deleted = []
        self.flush_count = 0

    def scalar(self, _statement):
        return self.values.pop(0)

    def add(self, value):
        self.added.append(value)

    def delete(self, value):
        self.deleted.append(value)

    def flush(self):
        self.flush_count += 1

    def begin_nested(self):
        return nullcontext()


def test_crawl_lease_metadata_enforces_site_scope_and_global_host_uniqueness():
    table = Base.metadata.tables["seo_crawl_leases"]
    foreign_keys = [
        tuple(element.parent.name for element in constraint.elements)
        for constraint in table.foreign_key_constraints
    ]
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("site_id", "tenant_id", "store_id") in foreign_keys
    assert ("host",) in unique_columns
    assert {"lease_token", "lease_expires_at", "crawl_id"} <= set(table.c.keys())


def test_acquire_crawl_lease_claims_one_host_and_tenant_slot():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    db = _Session([11, 33, 0, None])
    crawl_id = str(uuid4())
    grant = acquire_crawl_lease(
        db,
        tenant_id=11,
        store_id=22,
        site_id=33,
        host="Example.COM",
        crawl_id=crawl_id,
        now=now,
    )
    lease = db.added[0]
    assert grant.host == "example.com"
    assert grant.crawl_id == crawl_id
    assert len(grant.lease_token) == 64
    assert lease.tenant_id == 11 and lease.store_id == 22 and lease.site_id == 33
    assert lease.lease_expires_at == now + timedelta(seconds=180)



def test_acquire_normalizes_public_ipv6_host():
    db = _Session([11, 33, 0, None])
    grant = acquire_crawl_lease(
        db, tenant_id=11, store_id=22, site_id=33,
        host="2606:4700:4700::1111", crawl_id=str(uuid4()),
        now=datetime(2026, 11, 8, 10, 0, tzinfo=UTC),
    )
    assert grant.host == "2606:4700:4700::1111"


def test_acquire_rejects_a_host_already_leased_by_another_crawl():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    existing = SimpleNamespace(lease_expires_at=now + timedelta(seconds=30))
    db = _Session([11, 33, 0, existing])
    with pytest.raises(CrawlLeaseError, match="seo_crawler_host_busy"):
        acquire_crawl_lease(
            db, tenant_id=11, store_id=22, site_id=33,
            host="example.com", crawl_id=str(uuid4()), now=now,
        )


def test_acquire_enforces_tenant_concurrency_before_host_claim():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    db = _Session([11, 33, 1])
    with pytest.raises(CrawlLeaseError, match="seo_crawler_tenant_concurrency_limit"):
        acquire_crawl_lease(
            db, tenant_id=11, store_id=22, site_id=33,
            host="another.example.com", crawl_id=str(uuid4()),
            max_concurrent_per_tenant=1, now=now,
        )


def test_expired_host_lease_is_reclaimed_with_a_new_token():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    existing = SimpleNamespace(
        lease_expires_at=now - timedelta(seconds=1),
        tenant_id=99, store_id=98, site_id=97, crawl_id=str(uuid4()),
        lease_token="x" * 64, created_at=now - timedelta(minutes=5),
    )
    db = _Session([11, 33, 0, existing])
    grant = acquire_crawl_lease(
        db, tenant_id=11, store_id=22, site_id=33,
        host="example.com", crawl_id=str(uuid4()), now=now,
    )
    assert existing.tenant_id == 11
    assert existing.store_id == 22
    assert existing.site_id == 33
    assert existing.lease_token == grant.lease_token
    assert existing.lease_expires_at == grant.expires_at


def test_renew_and_release_require_the_current_lease_token():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    crawl_id = str(uuid4())
    grant = SimpleNamespace(
        host="example.com", crawl_id=crawl_id,
        lease_token="a" * 64, expires_at=now + timedelta(seconds=30),
    )
    row = SimpleNamespace(lease_expires_at=grant.expires_at)
    db = _Session([row])
    renewed = renew_crawl_lease(db, grant, lease_seconds=240, now=now)
    assert renewed.expires_at == now + timedelta(seconds=240)
    assert row.lease_expires_at == renewed.expires_at

    release_db = _Session([row])
    assert release_crawl_lease(release_db, renewed) is True
    assert release_db.deleted == [row]


def test_renew_rejects_lost_or_expired_lease():
    now = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    grant = SimpleNamespace(
        host="example.com", crawl_id=str(uuid4()),
        lease_token="b" * 64, expires_at=now,
    )
    db = _Session([None])
    with pytest.raises(CrawlLeaseError, match="seo_crawler_lease_lost"):
        renew_crawl_lease(db, grant, now=now)


@pytest.mark.parametrize("kwargs", [
    {"lease_seconds": 10},
    {"max_concurrent_per_tenant": 0},
    {"tenant_id": 0},
    {"crawl_id": "not-a-uuid"},
    {"host": "localhost"},
    {"host": "example.com/private"},
])
def test_acquire_rejects_invalid_lease_inputs(kwargs):
    values = {
        "tenant_id": 11,
        "store_id": 22,
        "site_id": 33,
        "host": "example.com",
        "crawl_id": str(uuid4()),
        "now": datetime(2026, 11, 8, 10, 0, tzinfo=UTC),
    }
    values.update(kwargs)
    with pytest.raises(CrawlLeaseError):
        acquire_crawl_lease(_Session([]), **values)
