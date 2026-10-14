"""Offline Render backend environment-key preservation audit for a Neon DB cutover.

Neon is NOT a destination for Render API environment variables. This command
audits the set of *variable names* before/after a proposed Render change,
without loading credentials or database URLs. It does NOT validate secret
value equality, change settings, run an application or connect to any service.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")
DATABASE_SELECTOR = {"DATABASE_URL", "DATABASE_URL_FILE"}
CRITICAL_FAMILIES = {
    "application_and_sessions": (
        "APP_ENV", "APPLICATION_SECRET", "APPLICATION_SECRET_FILE",
        "SESSION_COOKIE_NAME", "SESSION_COOKIE_SECURE",
    ),
    "meta_and_ig_encryption": (
        "META_APP_SECRET", "META_APP_SECRET_FILE", "META_VERIFY_TOKEN",
        "META_ACCESS_TOKEN", "META_ACCESS_TOKEN_FILE",
        "INSTAGRAM_TOKEN_ENCRYPTION_KEY",
        "INSTAGRAM_TOKEN_ENCRYPTION_KEY_FILE",
        "META_SEND_ENABLED", "META_WEBHOOK_RELAY_TARGET_URL",
        "META_OAUTH_RELAY_TARGET_URL",
    ),
    "payment_integrations": (
        "PAYEXA_API_KEY", "PAYEXA_CALLBACK_BASE_URL",
        "KPAY_ACCESS_TOKEN", "KPAY_CALLBACK_BASE_URL",
        "CARD_TRANSFER_CARD_NUMBER",
    ),
    "startup_writes": (
        "DIRECTPILOT_SEED_ON_START",
        "DIRECTPILOT_BOOTSTRAP_ADMIN_ON_START",
        "DIRECTPILOT_RESET_ADMIN_PASSWORD_ON_START",
        "DIRECTPILOT_APPROVE_PRODUCTION_CUSTOMER_PAYMENT_ON_START",
        "DIRECTPILOT_APPROVE_UAT_CUSTOMER_PAYMENT_ON_START",
        "DIRECTPILOT_RESET_UAT_CUSTOMER_PLAN_ON_START",
    ),
    "database_pooling": (
        "DATABASE_POOL_SIZE", "DATABASE_MAX_OVERFLOW",
        "DATABASE_POOL_TIMEOUT", "WEB_CONCURRENCY",
    ),
}


class UnsafeInventory(ValueError):
    pass


def parse_names(contents: str) -> frozenset[str]:
    keys: set[str] = set()
    for number, line in enumerate(contents.splitlines(), start=1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if not KEY.fullmatch(value):
            raise UnsafeInventory(
                f"Line {number} is not an environment NAME. "
                "Do not supply KEY=value or any secret data."
            )
        if value in keys:
            raise UnsafeInventory(f"Duplicate key name at line {number}")
        keys.add(value)
    if not keys:
        raise UnsafeInventory("No variable names provided")
    return frozenset(keys)


def check_preservation(before: frozenset[str], after: frozenset[str]) -> dict:
    if not DATABASE_SELECTOR.intersection(before):
        raise UnsafeInventory("Source inventory missing DATABASE_URL or DATABASE_URL_FILE")
    if not DATABASE_SELECTOR.intersection(after):
        raise UnsafeInventory("Target Render environment missing database selector")
    missing = sorted(before - after)
    new = sorted(after - before)
    return {
        "status": "PASS_NAMES_ONLY" if not missing else "BLOCKED_MISSING_NAMES",
        "source_key_count": len(before),
        "proposed_render_key_count": len(after),
        "missing_names": missing,
        "new_names": new,
        "critical_family_name_counts": {
            group: sum(1 for name in names if name in before)
            for group, names in CRITICAL_FAMILIES.items()
        },
        "secret_values_checked": False,
        "env_values_copied_to_neon": False,
        "production_database_url_changed": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--render-keys", type=Path, required=True,
                    help="Names only, one name per line; never use KEY=value")
    ap.add_argument("--proposed-render-keys", type=Path, required=True,
                    help="Proposed Render environment names, NOT Neon environment")
    args = ap.parse_args(argv)
    try:
        before = parse_names(args.render_keys.read_text(encoding="utf-8"))
        after = parse_names(args.proposed_render_keys.read_text(encoding="utf-8"))
        result = check_preservation(before, after)
    except (UnsafeInventory, OSError, UnicodeError) as exc:
        print(f"ENV_AUDIT_BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"ENV_KEY_PRESERVATION: {result['status']}")
    print("RENDER_ENV_KEYS_BEFORE:", result["source_key_count"])
    print("RENDER_ENV_KEYS_PROPOSED:", result["proposed_render_key_count"])
    print("MISSING_KEY_NAMES:", ",".join(result["missing_names"]) or "NONE")
    print("NEW_KEY_NAMES:", ",".join(result["new_names"]) or "NONE")
    print("KEY_VALUE_PARITY: NOT TESTED; verify via private Render UI/operator")
    print("NEON_VARIABLE_COPY: NOT APPLICABLE — Neon is database host only")
    print("PRODUCTION_DATABASE_URL: UNCHANGED BY THIS TOOL")
    return 0 if result["status"] == "PASS_NAMES_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
