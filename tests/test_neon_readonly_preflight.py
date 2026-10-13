"""Offline safety tests: no connection to Neon, Render, or UAT."""
import pytest
from tools.neon_readonly_preflight import (
    CHECKS, EXPECTED_HOST, EXPECTED_DATABASE, PreflightRejected,
    validate_target_url,
)


def test_exact_restored_neon_url_is_allowed():
    url = validate_target_url(
        f"postgresql://user:pass@{EXPECTED_HOST}/{EXPECTED_DATABASE}?sslmode=require"
    )
    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "require"


@pytest.mark.parametrize("url", [
    "sqlite:///local.db",
    "postgresql://user:pass@localhost/neondb",
    "postgresql://user:pass@dpg-any.oregon-postgres.render.com/directpilot_production_db",
    "postgresql://user:pass@ep-uat.c-4.us-west-2.aws.neon.tech/neondb",
    f"postgresql://user:pass@{EXPECTED_HOST}/uat",
    f"postgresql://user:pass@{EXPECTED_HOST}/{EXPECTED_DATABASE}?sslmode=disable",
    f"postgresql://user@{EXPECTED_HOST}/{EXPECTED_DATABASE}?sslmode=require",
])
def test_unsafe_connection_urls_are_rejected(url):
    with pytest.raises(PreflightRejected):
        validate_target_url(url)


def test_diagnostic_sql_is_read_only_by_construction():
    assert CHECKS
    for statement in CHECKS.values():
        assert statement.strip().upper().startswith("SELECT ")
        assert not any(
            forbidden in statement.upper()
            for forbidden in ("UPDATE ", "DELETE ", "DROP ", "INSERT ", "TRUNCATE ", "ALTER ")
        )
