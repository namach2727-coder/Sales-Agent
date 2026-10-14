"""Offline tests only. No Render or Neon network or Production writes."""
from datetime import datetime, timezone
import hashlib
import json

import pytest

from tools import production_final_sync as sync


def postgres_url(host: str, database: str, sslmode="require") -> str:
    return f"postgresql://operator:test_password@{host}:5432/{database}?sslmode={sslmode}"


def test_only_the_new_empty_neon_destination_is_permitted():
    d = sync.validate_destination(postgres_url(sync.TARGET_HOST, "directpilot_live"))
    assert d["PGDATABASE"] == "directpilot_live"
    assert d["PGSSLMODE"] == "require"


@pytest.mark.parametrize("host,db,sslmode", [
    (sync.TARGET_HOST, "neondb", "require"),
    ("ep-quiet-dew-ar9fhqml.c-4.us-west-2.aws.neon.tech", "neondb", "require"),
    ("dpg-test.oregon-postgres.render.com", "directpilot_production_db", "require"),
    ("localhost", "directpilot_live", "require"),
    (sync.TARGET_HOST, "directpilot_live", "disable"),
])
def test_reject_rehearsal_cross_environment_and_cleartext(host, db, sslmode):
    with pytest.raises(sync.SyncDenied):
        sync.validate_destination(postgres_url(host, db, sslmode))


def test_source_rejects_neon_not_render():
    with pytest.raises(sync.SyncDenied):
        sync.validate_source(postgres_url(sync.TARGET_HOST, "directpilot_production_db"))


def test_final_backup_requires_write_freeze_before_reading_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv(sync.SOURCE_ENV, raising=False)
    with pytest.raises(sync.SyncDenied, match="frozen"):
        sync.fresh_backup(tmp_path, confirmation="", client="local")


def test_final_restore_requires_protected_recovery_before_contacting_target(tmp_path, monkeypatch):
    monkeypatch.delenv(sync.TARGET_ENV, raising=False)
    with pytest.raises(sync.SyncDenied, match="Protected"):
        sync.restore_new_target(
            tmp_path / "unknown.dump", confirmation=sync.FREEZE,
            recovery="", approve=True, client="local",
        )


def test_unapproved_restore_is_blocked(tmp_path, monkeypatch):
    monkeypatch.delenv(sync.TARGET_ENV, raising=False)
    with pytest.raises(sync.SyncDenied, match="confirm-empty-target"):
        sync.restore_new_target(
            tmp_path / "unknown.dump", confirmation=sync.FREEZE,
            recovery=sync.RECOVERY, approve=False, client="local",
        )


def test_fresh_manifest_hash_and_age(tmp_path):
    f = tmp_path / "directpilot-final-example.dump"
    f.write_bytes(b"synthetic test data only")
    m = {
        "source": sync.SOURCE_DB,
        "target": sync.TARGET_DB,
        "filename": f.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        "size_bytes": f.stat().st_size,
        "source_freeze_declared_by_operator": True,
    }
    f.with_suffix(".manifest.json").write_text(json.dumps(m), encoding="utf-8")
    sync.manifest_verified(f)
    f.write_bytes(b"corrupted")
    with pytest.raises(sync.SyncDenied):
        sync.manifest_verified(f)


def test_empty_target_metadata_is_read_only(monkeypatch):
    seen = []
    def fake_command(tool, args, connection, mode=None):
        seen.append((tool, args))
        return "0\n"
    monkeypatch.setattr(sync.legacy, "command", fake_command)
    assert sync.empty_target({"PGDATABASE":sync.TARGET_DB}, mode="local") is True
    assert seen[0][0] == "psql"
    assert "SELECT COUNT(*)" in seen[0][1][-1]
    assert not any(token in seen[0][1][-1].upper() for token in (" DROP ", " DELETE ", " TRUNCATE "))


def test_unfrozen_restore_fails_closed_before_any_file_or_database_check(tmp_path):
    with pytest.raises(sync.SyncDenied, match="frozen"):
        sync.restore_new_target(
            tmp_path / "not-exist.dump", confirmation="NOT_FROZEN",
            recovery=sync.RECOVERY, approve=True, client="local",
        )
