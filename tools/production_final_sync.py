"""Operator-only scoped final backup and restore to NEW EMPTY Neon directpilot_live.

HARD SAFETY: neither this CLI nor the assistant can freeze all customer writes,
Meta webhooks, Payexa callbacks and background jobs. Do not execute until the
operator proves a durable source freeze, event replay and protected off-host
restore-tested backup. The current restored Neon neondb is NEVER overwritten.
No application secret, live DATABASE_URL, DNS or deployment is touched.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, unquote, urlsplit

from tools import production_db_transfer as legacy

SOURCE_ENV = "DIRECTPILOT_RENDER_SOURCE_URL"
TARGET_ENV = "DIRECTPILOT_NEON_TARGET_URL"
SOURCE_DB = "directpilot_production_db"
TARGET_DB = "directpilot_live"
TARGET_HOST = "ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech"
FREEZE = "ALL_CUSTOMER_WRITES_AND_WEBHOOKS_FROZEN"
RECOVERY = "OFFSITE_ENCRYPTED_BACKUP_RESTORE_TESTED"
MAX_AGE_SECONDS = 7200


class SyncDenied(Exception):
    pass


def validate_destination(raw: str) -> dict[str, str]:
    try:
        p = urlsplit(raw)
        db = unquote(p.path.lstrip("/"))
        host = (p.hostname or "").lower()
        port = p.port
        sslmode = parse_qs(p.query).get("sslmode", ["require"])[-1]
    except Exception:
        raise SyncDenied("Invalid private PostgreSQL destination URL") from None
    if p.scheme not in ("postgres", "postgresql"):
        raise SyncDenied("PostgreSQL URL required")
    if (host, db) != (TARGET_HOST, TARGET_DB):
        raise SyncDenied("Wrong destination: only fresh directpilot_live is permitted")
    if port not in (None, 5432) or not p.username or not p.password:
        raise SyncDenied("Invalid private destination credentials")
    if sslmode not in {"require", "verify-ca", "verify-full"}:
        raise SyncDenied("Encrypted TLS connection required")
    return {
        "PGHOST":host, "PGPORT":"5432", "PGDATABASE":TARGET_DB,
        "PGUSER":unquote(p.username), "PGPASSWORD":unquote(p.password),
        "PGSSLMODE":sslmode, "PGCONNECT_TIMEOUT":"15",
    }


def validate_source(raw: str) -> dict[str, str]:
    try:
        conn = legacy.connection_env(raw, source=True)
    except legacy.TransferError:
        raise SyncDenied("Wrong Render source or invalid credentials") from None
    if conn["PGDATABASE"] != SOURCE_DB:
        raise SyncDenied("Render source database differs")
    return conn


def frozen(confirmation: str) -> None:
    if confirmation != FREEZE:
        raise SyncDenied("Stop: all writes/Meta/Payexa/workers must be durably frozen")


def private_folder(path: Path) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise SyncDenied("Use an absolute non-symlink private folder outside repository")
    if path.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise SyncDenied("Never write customer DB dumps into Git repository")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def fresh_backup(folder: Path, *, confirmation: str, client: str | None) -> Path:
    frozen(confirmation)
    url = os.environ.get(SOURCE_ENV, "")
    if not url:
        raise SyncDenied("Missing local private source URL")
    source = validate_source(url)
    root = private_folder(folder)
    mode = client or legacy.resolve_mode()
    name = "directpilot-final-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".dump"
    archive = root / name
    if archive.exists():
        raise SyncDenied("Archive already exists; never overwrite")
    arg = f"/backup/{name}" if mode == "docker" else str(archive)
    try:
        legacy.command("pg_dump",
            ["--format=custom", "--compress=9", "--no-owner", "--no-privileges", "--file", arg],
            source, volume=root, mode=mode)
        if not archive.is_file() or archive.stat().st_size == 0:
            raise SyncDenied("Archive missing or empty")
        toc = legacy.command("pg_restore", ["--list", arg], {}, volume=root, mode=mode)
        if "TABLE" not in toc or "TABLE DATA" not in toc:
            raise SyncDenied("Archive missing application tables or rows")
        manifest = {
            "source": SOURCE_DB, "target": TARGET_DB, "filename": name,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": legacy.file_digest(archive),
            "size_bytes": archive.stat().st_size,
            "source_freeze_declared_by_operator": True,
            "restore_executed": False,
        }
        sidecar = archive.with_suffix(".manifest.json")
        with sidecar.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
        if os.name != "nt":
            archive.chmod(0o600)
            sidecar.chmod(0o600)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    print("FINAL_ARCHIVE_PASS (sensitive file retained PRIVATELY).")
    print("Next: encrypt/secure offsite and independently RESTORE TEST the backup.")
    return archive


def manifest_verified(path: Path) -> None:
    if not path.is_file() or path.suffix != ".dump":
        raise SyncDenied("Private backup missing")
    try:
        m = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(m["created_at_utc"])).total_seconds()
    except Exception:
        raise SyncDenied("Invalid private backup manifest") from None
    if (m.get("source") != SOURCE_DB or m.get("target") != TARGET_DB
            or m.get("filename") != path.name
            or m.get("size_bytes") != path.stat().st_size
            or m.get("sha256") != legacy.file_digest(path)
            or m.get("source_freeze_declared_by_operator") is not True):
        raise SyncDenied("Manifest/checksum does not match exact frozen-source archive")
    if not (0 <= age <= MAX_AGE_SECONDS):
        raise SyncDenied("Final backup older than two hours; fresh freeze/dump needed")


def empty_target(target: dict[str, str], *, mode: str) -> bool:
    sql = ("SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
           "WHERE n.nspname='public' AND c.relkind IN ('r','p','S','v','m','f','i','I')")
    data = legacy.command(
        "psql", ["-X","-t","-A","-v","ON_ERROR_STOP=1","-c",sql],target,mode=mode
    ).strip()
    if not data.isdigit():
        raise SyncDenied("Unexpected empty-database preflight result")
    return int(data) == 0


def restore_new_target(path: Path, *, confirmation: str, recovery: str,
                       approve: bool, client: str | None) -> None:
    frozen(confirmation)
    if recovery != RECOVERY:
        raise SyncDenied("Protected off-provider recovery copy and restore test REQUIRED")
    if not approve:
        raise SyncDenied("Missing --confirm-empty-target-restore")
    raw = os.environ.get(TARGET_ENV, "")
    if not raw:
        raise SyncDenied("Private Neon FINAL target URL missing")
    target = validate_destination(raw)
    manifest_verified(path)
    mode = client or legacy.resolve_mode()
    arg = f"/backup/{path.name}" if mode == "docker" else str(path)
    toc = legacy.command("pg_restore", ["--list", arg], {}, volume=path.parent, mode=mode)
    if "TABLE DATA" not in toc:
        raise SyncDenied("Not a complete database archive")
    if not empty_target(target, mode=mode):
        raise SyncDenied("Target NOT EMPTY; do not DROP/CLEAN/overwrite anything")
    legacy.command(
        "pg_restore", ["--exit-on-error", "--single-transaction", "--no-owner",
                       "--no-privileges", "--dbname", TARGET_DB, arg],
        target, volume=path.parent, mode=mode)
    data = legacy.command(
        "psql", ["-X","-t","-A","-v","ON_ERROR_STOP=1","-c",
                 "SELECT COUNT(*) FROM information_schema.tables "
                 "WHERE table_schema='public' AND table_type='BASE TABLE'"],
        target, mode=mode).strip()
    if not data.isdigit() or int(data) < 1:
        raise SyncDenied("Restore completed but application table integrity FAILED")
    print("FRESH_NEON_RESTORE_PASS; table_count=" + data)
    print("NO_CUTOVER: validate fresh Render-vs-Neon row AND CONTENT parity first.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("backup", "restore"))
    ap.add_argument("--folder", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--client", choices=("local", "docker"))
    ap.add_argument("--freeze-confirmation", default="")
    ap.add_argument("--recovery-confirmation", default="")
    ap.add_argument("--confirm-empty-target-restore", action="store_true")
    args = ap.parse_args()
    try:
        if args.action == "backup":
            if args.folder is None:
                raise SyncDenied("--folder required")
            fresh_backup(args.folder, confirmation=args.freeze_confirmation, client=args.client)
        else:
            if args.archive is None:
                raise SyncDenied("--archive required")
            restore_new_target(
                args.archive, confirmation=args.freeze_confirmation,
                recovery=args.recovery_confirmation,
                approve=args.confirm_empty_target_restore, client=args.client,
            )
    except (SyncDenied, legacy.TransferError, OSError, ValueError) as exc:
        print("FINAL_SYNC_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
