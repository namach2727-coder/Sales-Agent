"""Safely seed system-only reference data on the approved dedicated Neon UAT DB."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

from tools.bootstrap_neon_uat_schema import inspect_target, validated_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=("dry-run", "seed"))
    args = parser.parse_args()

    try:
        url = validated_url(os.environ.get("NEON_UAT_DIRECT_DATABASE_URL", ""))
        count, revision = inspect_target(url)
        head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        if count < 2 or not head or revision != head:
            raise ValueError("UAT database is not at Alembic head")

        env = dict(os.environ)
        env["DATABASE_URL"] = url
        env["APP_ENV"] = "development"
        # Production-safe profile selects only approved, credential-free global seeds.
        cmd = [sys.executable, "-m", "tools.seed_data",
               "--profile", "production", "--use-configured-database"]
        if args.action == "dry-run":
            cmd.append("--dry-run")

        print(f"Approved Neon UAT target confirmed; tables={count}; head={head}; action={args.action}", flush=True)
        subprocess.run(cmd, env=env, check=True)
        print(f"UAT SEED {args.action.upper()} PASS", flush=True)
        return 0
    except Exception:
        # Avoid printing exceptions potentially containing secrets or URLs.
        print("UAT SEED STOPPED; inspect safe job output", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
