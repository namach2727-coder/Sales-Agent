"""Safe read-only application database preflight for restored Neon Production.

Operator-only CLI: uses the already restored Neon database, never launches FastAPI,
never runs Alembic, never seeds data, and never invokes payment/Meta integrations.
Do NOT use this tool as live cutover acceptance without a fresh source delta.
"""
from __future__ import annotations

import getpass
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

EXPECTED_HOST = "ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech"
EXPECTED_DATABASE = "neondb"
EXPECTED_VERSION = "0025_trial_three_days"
EXPECTED_TABLES = 82
EXPECTED_SEQUENCES = 76
EXPECTED_INDEXES = 522
EXPECTED_CONSTRAINTS = 427

NEON_URL_VAR = "DIRECTPILOT_NEON_READONLY_URL"

class PreflightRejected(RuntimeError):
    pass


def validate_target_url(raw: str) -> URL:
    """Allow only the precisely verified restored Neon database, via TLS."""
    try:
        url = make_url(raw.strip())
    except Exception:
        raise PreflightRejected("Invalid PostgreSQL URL") from None
    if url.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise PreflightRejected("Only psycopg PostgreSQL URLs are accepted")
    if (
        (url.host or "").lower() != EXPECTED_HOST
        or url.database != EXPECTED_DATABASE
        or url.port not in (None, 5432)
    ):
        raise PreflightRejected("Refusing anything except verified Neon Production target")
    if not url.username or not url.password:
        raise PreflightRejected("Missing database credentials")
    if url.query.get("sslmode", "require") not in {"require", "verify-ca", "verify-full"}:
        raise PreflightRejected("TLS is mandatory")
    return url.set(drivername="postgresql+psycopg", query={
        **url.query,
        "sslmode": url.query.get("sslmode", "require"),
    })


CHECKS = {
    "tables": """SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname='public' AND c.relkind IN ('r','p')""",
    "sequences": """SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='public' AND c.relkind='S'""",
    "indexes": """SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                  WHERE n.nspname='public' AND c.relkind IN ('i','I')""",
    "constraints": """SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
                      WHERE n.nspname='public' AND c.contype<>'n'""",
    "invalid_indexes": """SELECT count(*) FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid
                          JOIN pg_namespace n ON n.oid=c.relnamespace
                          WHERE n.nspname='public' AND NOT i.indisvalid""",
    "unvalidated_constraints": """SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
                                  WHERE n.nspname='public' AND NOT c.convalidated""",
    "invalid_subscription_periods": """SELECT count(*) FROM tenant_subscriptions
                                       WHERE starts_at IS NOT NULL AND current_period_end IS NOT NULL
                                       AND current_period_end < starts_at""",
    "orphan_subscriptions": """SELECT count(*) FROM tenant_subscriptions s
                              LEFT JOIN tenants t ON s.tenant_id=t.id WHERE t.id IS NULL""",
    "orphan_orders": """SELECT count(*) FROM subscription_orders o
                       LEFT JOIN saas_plans p ON p.id=o.plan_id
                       WHERE o.plan_id IS NOT NULL AND p.id IS NULL""",
    "orphan_payments": """SELECT count(*) FROM manual_payments m
                         LEFT JOIN subscription_orders o ON o.id=m.order_id
                         WHERE m.order_id IS NOT NULL AND o.id IS NULL""",
}

AGGREGATES = {
    "tenants": "SELECT count(*) FROM tenants",
    "stores": "SELECT count(*) FROM stores",
    "users": "SELECT count(*) FROM user_identities",
    "subscriptions": "SELECT count(*) FROM tenant_subscriptions",
    "orders": "SELECT count(*) FROM subscription_orders",
    "manual_payments": "SELECT count(*) FROM manual_payments",
    "instagram_connections": "SELECT count(*) FROM instagram_connections",
    "webhook_deliveries": "SELECT count(*) FROM instagram_webhook_deliveries",
}


def run_preflight(raw_url: str) -> dict[str, object]:
    url = validate_target_url(raw_url)
    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        pool_timeout=10,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": 10,
            # Every connection is read-only at the SERVER level, not merely an
            # agreement to avoid writing SQL.
            "options": "-c default_transaction_read_only=on -c statement_timeout=15000",
        },
    )
    try:
        # Verify SQLAlchemy uses psycopg and the actual database identity.
        # Do not import FastAPI or app.database: they can register startup work.
        from app.operations import expected_alembic_head

        with engine.connect() as con:
            if con.scalar(text("SELECT current_setting('transaction_read_only')")) != "on":
                raise PreflightRejected("Database connection is NOT read-only")
            if con.scalar(text("SELECT current_database()")) != EXPECTED_DATABASE:
                raise PreflightRejected("Unexpected current database")
            version_num = int(con.scalar(text("SHOW server_version_num")))
            if not 180000 <= version_num < 190000:
                raise PreflightRejected("Expected PostgreSQL 18")
            current = con.scalar(text("SELECT version_num FROM public.alembic_version"))
            if current != EXPECTED_VERSION or current != expected_alembic_head():
                raise PreflightRejected("Alembic revision mismatch")
            metrics = {key: int(con.scalar(text(query))) for key, query in CHECKS.items()}
            target = {"tables": EXPECTED_TABLES, "sequences": EXPECTED_SEQUENCES,
                      "indexes": EXPECTED_INDEXES, "constraints": EXPECTED_CONSTRAINTS}
            for key, expected in target.items():
                if metrics[key] != expected:
                    raise PreflightRejected(f"Unexpected {key} count; stop before cutover")
            for key, count in metrics.items():
                if key not in target and count:
                    raise PreflightRejected(f"Integrity violation: {key}={count}")
            trial_rows = con.execute(text("""
                SELECT code, duration_days FROM saas_plans
                WHERE code IN ('TRIAL','AUTOMATION_TRIAL','AI_ASSISTANT_TRIAL')
                ORDER BY code
            """)).all()
            trials = {str(code): int(days) for code, days in trial_rows}
            if trials != {"AI_ASSISTANT_TRIAL": 3, "AUTOMATION_TRIAL": 3, "TRIAL": 3}:
                raise PreflightRejected("Three-day trial catalog mismatch")
            counts = {key: int(con.scalar(text(query))) for key, query in AGGREGATES.items()}
            return {"sqlalchemy_driver": engine.dialect.driver,
                    "postgresql_major": version_num // 10000,
                    "migration": current,
                    "integrity_checks": metrics,
                    "business_table_counts": counts,
                    "three_day_trial_catalog": "PASS",
                    "connection_read_only": True,
                    "external_side_effects": "NONE",
                    "production_cutover": "NOT_PERFORMED"}
    finally:
        engine.dispose()


def main() -> int:
    raw_url = os.environ.get(NEON_URL_VAR)
    if not raw_url:
        raw_url = getpass.getpass("Paste Neon Production DIRECT database URL (hidden): ")
    if not raw_url:
        print("BLOCKED: Neon URL missing", file=sys.stderr)
        return 2
    try:
        r = run_preflight(raw_url)
        print("NEON_READONLY_PREFLIGHT: PASS")
        for name, value in r.items():
            print(f"{name.upper()}: {value}")
        print("Live API, Render Production, UAT and database rows were NOT modified.")
        return 0
    except Exception:
        # Avoid printing raw SQLAlchemy/psycopg exceptions (may contain credentials,
        # query parameters or database identifiers).
        print("NEON_READONLY_PREFLIGHT: FAIL; see local diagnostics securely; no retry side effects", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
