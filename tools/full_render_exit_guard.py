"""Fail-closed guard for proposed non-Render runtime. No DB connections.

Production destination is a PROPOSED new DB, not yet created. UAT is
on its own independent existing Neon project. Running this does not authorize
a live change, and never prints credentials.
"""
from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy.engine import make_url

PROD_HOST = "ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech"
PROD_DB = "directpilot_live"
UAT_HOST = "ep-quiet-dew-ar9fhqml.c-4.us-west-2.aws.neon.tech"
UAT_DB = "neondb"
ONE_SHOT_FLAGS = (
    "DIRECTPILOT_SEED_ON_START",
    "DIRECTPILOT_BOOTSTRAP_ADMIN_ON_START",
    "DIRECTPILOT_RESET_ADMIN_PASSWORD_ON_START",
    "DIRECTPILOT_RESET_UAT_CUSTOMER_PLAN_ON_START",
    "DIRECTPILOT_APPROVE_UAT_CUSTOMER_PAYMENT_ON_START",
    "DIRECTPILOT_APPROVE_PRODUCTION_CUSTOMER_PAYMENT_ON_START",
)
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

class UnsafePortableRuntime(ValueError):
    pass

def check_target(profile: str, database_url: str, values: dict[str, str]) -> str:
    if profile not in {"production", "uat"}:
        raise UnsafePortableRuntime("Profile must be production or uat")
    try:
        target = make_url(database_url)
    except Exception:
        raise UnsafePortableRuntime("Malformed database connection URL") from None
    expected = (PROD_HOST, PROD_DB) if profile == "production" else (UAT_HOST, UAT_DB)
    if target.drivername not in {"postgresql", "postgresql+psycopg"}:
        raise UnsafePortableRuntime("PostgreSQL psycopg required")
    if (target.host or "").lower() != expected[0] or target.database != expected[1]:
        raise UnsafePortableRuntime("Wrong DB host or DB name for environment; denied")
    if not target.username or not target.password or target.port not in (None, 5432):
        raise UnsafePortableRuntime("Invalid DB credentials or port")
    if target.query.get("sslmode", "require") not in {"require", "verify-ca", "verify-full"}:
        raise UnsafePortableRuntime("TLS required")
    for name in ONE_SHOT_FLAGS:
        if values.get(name, "").strip().lower() in TRUE_VALUES:
            raise UnsafePortableRuntime("Unsafe one-shot writer enabled: " + name)
    if values.get("META_SEND_ENABLED", "false").strip().lower() in TRUE_VALUES:
        if values.get("FULL_EXIT_ENABLE_META_SEND", "").strip().lower() != "true":
            raise UnsafePortableRuntime("Outbound Meta sends require separate cutover gate")
    if values.get("APP_ENV", "") != profile:
        raise UnsafePortableRuntime("Runtime APP_ENV mismatch")
    if values.get("FULL_EXIT_SAFE_START", "").strip().lower() != "true":
        raise UnsafePortableRuntime("Missing explicit, scoped safe-start operator gate")
    return f"PORTABLE_GUARD_PASS: profile={profile}, db_name={target.database}"

def main() -> int:
    profile = os.getenv("APP_ENV", "")
    raw = os.getenv("DATABASE_URL", "")
    path = os.getenv("DATABASE_URL_FILE", "")
    if path and raw:
        print("PORTABLE_GUARD_BLOCKED: ambiguous DB URL and URL_FILE configured together")
        return 2
    if path and not raw:
        p = Path(path).resolve()
        if p.is_relative_to(Path("/app")):
            print("PORTABLE_GUARD_BLOCKED: credentials file inside app tree")
            return 2
        try:
            raw = p.read_text(encoding="utf-8").strip()
        except OSError:
            print("PORTABLE_GUARD_BLOCKED: cannot read private DB URL file")
            return 2
    try:
        print(check_target(profile, raw, dict(os.environ)))
        return 0
    except UnsafePortableRuntime as exc:
        print(f"PORTABLE_GUARD_BLOCKED: {exc}")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
