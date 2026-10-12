from __future__ import annotations

import pytest
from sqlalchemy.engine import make_url

from tools.bootstrap_neon_uat_schema import (
    EXPECTED_DB,
    EXPECTED_HOST,
    EXPECTED_ROLE,
    validated_url,
)

GOOD = (
    f"postgresql://{EXPECTED_ROLE}:test-password@{EXPECTED_HOST}/"
    f"{EXPECTED_DB}?sslmode=require&channel_binding=require"
)


def test_accept_direct_neon_connection_using_psycopg3() -> None:
    normalized = make_url(validated_url(GOOD))
    assert normalized.drivername == "postgresql+psycopg"
    assert normalized.host == EXPECTED_HOST
    assert normalized.database == EXPECTED_DB
    assert normalized.password == "test-password"
    assert normalized.query["sslmode"] == "require"


@pytest.mark.parametrize(
    "unsafe",
    [
        "",
        GOOD.replace(EXPECTED_HOST, "external.render.com"),
        GOOD.replace(EXPECTED_HOST, EXPECTED_HOST.replace("ep-", "ep-other-")),
        GOOD.replace(EXPECTED_HOST, "ep-quiet-dew-ar9fhqml-pooler.c-4.us-west-2.aws.neon.tech"),
        GOOD.replace(f"/{EXPECTED_DB}", "/directpilot_production_db"),
        GOOD.replace(EXPECTED_ROLE, "render_production_owner"),
        GOOD.replace("sslmode=require", "sslmode=disable"),
        GOOD.replace("postgresql://", "sqlite:///"),
    ],
)
def test_reject_every_unapproved_target(unsafe: str) -> None:
    with pytest.raises(ValueError):
        validated_url(unsafe)


def test_reject_missing_password() -> None:
    with pytest.raises(ValueError, match="credentials"):
        validated_url(GOOD.replace(":test-password@", "@"))
