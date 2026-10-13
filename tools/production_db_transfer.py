"""Guarded operator-only backup and isolated restore for DirectPilot.

Run on your own trusted workstation. Requires Python 3.10+ and either the
PostgreSQL 18 client tools or Docker Desktop. No app config or live DB changed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit, parse_qs

SOURCE_ENV = "DIRECTPILOT_RENDER_SOURCE_URL"
TARGET_ENV = "DIRECTPILOT_NEON_TARGET_URL"
EXPECTED_SOURCE_DATABASE = "directpilot_production_db"
EXPECTED_TARGET_HOST = "ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech"
EXPECTED_TARGET_DATABASE = "neondb"
IMAGE = "postgres:18"


class TransferError(RuntimeError):
    pass


def connection_env(value: str, *, source: bool) -> dict[str, str]:
    """Separate PG credentials from command arguments and check exact scope."""
    parsed = urlsplit(value)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise TransferError("Expected PostgreSQL connection URL")
    host = (parsed.hostname or "").lower()
    database = unquote(parsed.path.lstrip("/"))
    if source:
        if not (host.endswith(".render.com") and database == EXPECTED_SOURCE_DATABASE):
            raise TransferError("Source must be Render Production, never UAT")
    elif host != EXPECTED_TARGET_HOST or database != EXPECTED_TARGET_DATABASE:
        raise TransferError("Target must be the verified independent Neon Production endpoint")
    if not parsed.username or parsed.password is None or parsed.port not in (None, 5432):
        raise TransferError("Invalid PostgreSQL username/password/port")
    sslmode = parse_qs(parsed.query).get("sslmode", ["require"])[-1]
    if sslmode not in ("require", "verify-ca", "verify-full"):
        raise TransferError("SSL must be enabled")
    return {
        "PGHOST": host,
        "PGPORT": str(parsed.port or 5432),
        "PGUSER": unquote(parsed.username),
        "PGPASSWORD": unquote(parsed.password),
        "PGDATABASE": database,
        "PGSSLMODE": sslmode,
        "PGCONNECT_TIMEOUT": "15",
    }


def resolve_mode() -> str:
    if all(shutil.which(x) for x in ("pg_dump", "pg_restore", "psql")):
        return "local"
    if shutil.which("docker"):
        return "docker"
    raise TransferError("Install PostgreSQL 18 client tools or start Docker Desktop")


def command(tool: str, args: list[str], env: dict[str, str], *,
            volume: Path | None = None, mode: str | None = None) -> str:
    mode = mode or resolve_mode()
    process_env = {**os.environ, **env}
    if mode == "local":
        argv = [tool, *args]
    elif mode == "docker":
        argv = ["docker", "run", "--rm"]
        for name in env:
            argv.extend(["--env", name])  # inherit without exposing values in argv
        if volume is not None:
            argv.extend(["--mount", f"type=bind,source={volume.resolve()},target=/backup"])
        argv.extend([IMAGE, tool, *args])
    else:
        raise TransferError("Unknown PostgreSQL client mode")
    try:
        result = subprocess.run(argv, env=process_env, capture_output=True,
                                text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired):
        raise TransferError(f"{tool} did not complete; check Docker and network access") from None
    if result.returncode:
        # Do not echo stderr: some clients/plugins can include connection metadata.
        raise TransferError(f"{tool} failed (exit {result.returncode}); check credentials, allowlist and PostgreSQL compatibility")
    return result.stdout


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def backup(folder: Path, *, mode: str | None = None) -> Path:
    url = os.environ.get(SOURCE_ENV)
    if not url:
        raise TransferError(f"Set {SOURCE_ENV} locally; never share the value in chat")
    pg = connection_env(url, source=True)
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    filename = f"directpilot-production-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.dump"
    target = folder / filename
    if target.exists():
        raise TransferError("Existing dump; refusing to overwrite")
    client = mode or resolve_mode()
    archive_arg = f"/backup/{filename}" if client == "docker" else str(target)
    try:
        command("pg_dump", ["--format=custom", "--compress=9", "--no-owner",
                            "--no-privileges", "--file", archive_arg], pg,
                volume=folder, mode=client)
        if not target.is_file() or not target.stat().st_size:
            raise TransferError("Dump missing or zero bytes")
        toc = command("pg_restore", ["--list", archive_arg], {},
                      volume=folder, mode=client)
        if "TABLE" not in toc:
            raise TransferError("No table entries in archive")
        manifest = {
            "source": EXPECTED_SOURCE_DATABASE,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "filename": filename, "size_bytes": target.stat().st_size,
            "sha256": file_digest(target), "archive_listing_verified": True,
            "status": "offline backup only; no cutover",
        }
        sidecar = target.with_suffix(".manifest.json")
        sidecar.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        if os.name != "nt":
            target.chmod(0o600)
            sidecar.chmod(0o600)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    print(f"BACKUP PASS: {filename}; {target.stat().st_size} bytes")
    print(f"PRIVATE DIRECTORY: {folder.resolve()}")
    print("Copy to encrypted independent storage; do NOT upload archive to GitHub/chat")
    return target


def verify(path: Path, *, mode: str | None = None) -> None:
    if not path.is_file():
        raise TransferError("Dump missing")
    sidecar = path.with_suffix(".manifest.json")
    if not sidecar.is_file():
        raise TransferError("Backup manifest missing")
    manifest = json.loads(sidecar.read_text(encoding="utf-8"))
    if (path.name != manifest.get("filename")
            or path.stat().st_size != manifest.get("size_bytes")
            or file_digest(path) != manifest.get("sha256")):
        raise TransferError("Archive SHA-256/name/size does not match manifest")
    client = mode or resolve_mode()
    archive_arg = f"/backup/{path.name}" if client == "docker" else str(path)
    command("pg_restore", ["--list", archive_arg], {}, volume=path.parent, mode=client)
    print(f"ARCHIVE + SHA-256 PASS: {path.name}")


def restore(path: Path, *, confirm: bool, mode: str | None = None) -> None:
    if not confirm:
        raise TransferError("Explicit --confirm-isolated-restore required")
    url = os.environ.get(TARGET_ENV)
    if not url:
        raise TransferError(f"Set {TARGET_ENV} locally; never share the value in chat")
    pg = connection_env(url, source=False)
    verify(path, mode=mode)
    client = mode or resolve_mode()
    sql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"
    count = command("psql", ["-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1",
                             "-c", sql], pg, mode=client).strip()
    if count != "0":
        raise TransferError("Neon target not empty; refusing potentially destructive restore")
    archive_arg = f"/backup/{path.name}" if client == "docker" else str(path)
    command("pg_restore", ["--exit-on-error", "--single-transaction",
                           "--no-owner", "--no-privileges",
                           "--dbname", EXPECTED_TARGET_DATABASE, archive_arg],
            pg, volume=path.parent, mode=client)
    count = command("psql", ["-X", "-q", "-t", "-A", "-v",
                             "ON_ERROR_STOP=1", "-c", sql], pg, mode=client).strip()
    if not count.isdigit() or int(count) < 1:
        raise TransferError("Restore did not produce application tables")
    print(f"ISOLATED NEON RESTORE PASS: {count} tables; Production connection unchanged")
    print("Complete data reconciliation and smoke tests before any cutover")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "verify", "restore"))
    parser.add_argument("--folder", type=Path,
                        default=Path.home() / "DirectPilot-Private-Backups")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--confirm-isolated-restore", action="store_true")
    parser.add_argument("--client", choices=("local", "docker"))
    args = parser.parse_args()
    try:
        if args.action == "backup":
            backup(args.folder, mode=args.client)
        elif args.action == "verify":
            if args.archive is None:
                raise TransferError("--archive required")
            verify(args.archive, mode=args.client)
        else:
            if args.archive is None:
                raise TransferError("--archive required")
            restore(args.archive, confirm=args.confirm_isolated_restore, mode=args.client)
    except TransferError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
