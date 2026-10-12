"""Guarded one-time schema initialization of DirectPilot's dedicated Neon UAT database.

Never accepts a Production or pooled connection. The only mutation is Alembic
upgrade head on the known, newly provisioned Neon target. No production data,
sessions, credentials or Meta connections are copied.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

EXPECTED_HOST = "ep-quiet-dew-ar9fhqml.c-4.us-west-2.aws.neon.tech"
EXPECTED_DB = "neondb"
EXPECTED_ROLE = "neondb_owner"


def validated_url(raw: str) -> str:
    """Return a psycopg3 SQLAlchemy URL; never log or expose the password."""
    if not raw.strip():
        raise ValueError("NEON_UAT_DIRECT_DATABASE_URL is missing")
    url = make_url(raw)
    if url.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise ValueError("Expected a PostgreSQL connection URL")
    if url.host != EXPECTED_HOST or url.database != EXPECTED_DB:
        raise ValueError("Target host/database is not the approved Neon UAT project")
    if url.username != EXPECTED_ROLE or not url.password:
        raise ValueError("Neon UAT owner credentials are missing or unexpected")
    if url.query.get("sslmode") not in {"require", "verify-full"}:
        raise ValueError("Secure TLS mode is required")
    if "-pooler" in (url.host or ""):
        raise ValueError("Migration requires direct, unpooled Neon connection")
    return url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)


def inspect_target(url: str) -> tuple[int, str | None]:
    engine = create_engine(url, connect_args={"connect_timeout": 15}, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            name = conn.execute(text("select current_database()")).scalar_one()
            role = conn.execute(text("select current_user")).scalar_one()
            if name != EXPECTED_DB or role != EXPECTED_ROLE:
                raise ValueError("Connected PostgreSQL identity does not match Neon UAT")
            tables = inspect(conn).get_table_names(schema="public")
            version = None
            if "alembic_version" in tables:
                versions = conn.execute(text("select version_num from alembic_version")).scalars().all()
                if len(versions) != 1:
                    raise ValueError("Unexpected Alembic version rows")
                version = versions[0]
            return len(tables), version
    finally:
        engine.dispose()


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--action", choices=("preflight", "migrate"), required=True)
    parsed = args.parse_args()
    try:
        url = validated_url(os.getenv("NEON_UAT_DIRECT_DATABASE_URL", ""))
        count, version = inspect_target(url)
        expected_head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        if not expected_head:
            raise ValueError("No Alembic head is defined")
        print(f"Target verified: Neon UAT / {EXPECTED_DB}; tables={count}; "
              f"alembic_current={version or 'empty'}; expected_head={expected_head}")
        if parsed.action == "preflight":
            print("PREFLIGHT PASS: no database changes made")
            return 0
        if count:
            raise ValueError("Refusing migration: database is not empty. Review the current tables first.")
        env = dict(os.environ)
        env["DATABASE_URL"] = url
        env["APP_ENV"] = "development"  # Alembic only, no deployed service runtime or seed.
        # Neither hostname nor credentials are written to output.
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                       env=env, check=True)
        after_count, after_version = inspect_target(url)
        if after_count < 2 or after_version != expected_head:
            raise ValueError("Migration executed but final schema/head validation failed")
        print(f"MIGRATION PASS: Neon UAT tables={after_count}, head={after_version}")
        print("No seeds, real customer data, Meta credentials or service settings were modified.")
        return 0
    except Exception as exc:
        # Do not stringify driver errors: they can contain the connection URL.
        print(f"STOPPED: {type(exc).__name__}; review migration logs without exposing secrets",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
