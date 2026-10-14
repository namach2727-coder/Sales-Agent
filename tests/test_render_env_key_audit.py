"""Offline tests; no credentials or networks."""
import pytest
from tools.render_env_key_audit import (
    UnsafeInventory, parse_names, check_preservation,
)


def test_only_names_allowed():
    assert parse_names("DATABASE_URL\nAPP_ENV\nMETA_SEND_ENABLED\n") == {
        "DATABASE_URL", "APP_ENV", "META_SEND_ENABLED",
    }
    with pytest.raises(UnsafeInventory):
        parse_names("DATABASE_URL=postgresql://user:password@host/database")


@pytest.mark.parametrize("body", [
    "DATABASE_URL\nDATABASE_URL\n",
    " ",
    "app_env\n",
    "META-API-KEY\n",
    "META_APP_SECRET:VALUE\n",
])
def test_reject_unsafe_or_ambiguous_input(body):
    with pytest.raises(UnsafeInventory):
        parse_names(body)


def test_all_existing_render_key_names_preserved():
    source = parse_names("DATABASE_URL\nAPP_ENV\nAPPLICATION_SECRET\nMETA_APP_SECRET\nPAYEXA_API_KEY\n")
    proposed = parse_names("DATABASE_URL\nAPP_ENV\nAPPLICATION_SECRET\nMETA_APP_SECRET\nPAYEXA_API_KEY\n")
    report = check_preservation(source, proposed)
    assert report["status"] == "PASS_NAMES_ONLY"
    assert not report["secret_values_checked"]
    assert not report["env_values_copied_to_neon"]
    assert not report["production_database_url_changed"]


def test_missing_existing_secret_keys_fail():
    source = parse_names("DATABASE_URL\nMETA_APP_SECRET\nINSTAGRAM_TOKEN_ENCRYPTION_KEY\n")
    proposed = parse_names("DATABASE_URL\nMETA_APP_SECRET\n")
    result = check_preservation(source, proposed)
    assert result["status"] == "BLOCKED_MISSING_NAMES"
    assert result["missing_names"] == ["INSTAGRAM_TOKEN_ENCRYPTION_KEY"]


def test_database_url_file_selectors_supported():
    before = parse_names("DATABASE_URL_FILE\nAPP_ENV")
    after = parse_names("DATABASE_URL_FILE\nAPP_ENV")
    assert check_preservation(before, after)["status"] == "PASS_NAMES_ONLY"


def test_database_selector_required():
    with pytest.raises(UnsafeInventory):
        check_preservation(frozenset({"APP_ENV"}), frozenset({"APP_ENV"}))
    with pytest.raises(UnsafeInventory):
        check_preservation(frozenset({"DATABASE_URL"}), frozenset({"APP_ENV"}))
