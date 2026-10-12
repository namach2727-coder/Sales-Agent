"""Guarded first administrator bootstrap for dedicated DirectPilot Neon UAT."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from email.utils import parseaddr

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from tools.bootstrap_neon_uat_schema import inspect_target, validated_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    try:
        email = args.email.strip().lower()
        if not email or len(email) > 254 or parseaddr(email)[1] != email or "@" not in email:
            raise ValueError("Invalid admin email")
        password = os.environ.get("NEON_UAT_ADMIN_BOOTSTRAP_PASSWORD", "")
        if len(password) < 12:
            raise ValueError("UAT admin password secret missing or too short")
        url = validated_url(os.environ.get("NEON_UAT_DIRECT_DATABASE_URL", ""))
        count, current = inspect_target(url)
        head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        if count < 2 or current != head:
            raise ValueError("Target schema not at Alembic head")
        engine = create_engine(url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                n_users = conn.execute(text("SELECT count(*) FROM user_identities")).scalar_one()
                n_admins = conn.execute(text("SELECT count(*) FROM auth_platform_role_assignments WHERE role_code='platform_super_admin' AND status='active'")).scalar_one()
                n_roles = conn.execute(text("SELECT count(*) FROM auth_roles")).scalar_one()
                if n_users != 0 or n_admins != 0 or n_roles == 0:
                    raise ValueError("Refusing bootstrap: identities or admin already exist, or seed is missing")
        finally:
            engine.dispose()
        env = dict(os.environ)
        env["DATABASE_URL"] = url
        env["APP_ENV"] = "development"
        env["BOOTSTRAP_ADMIN_PASSWORD"] = password
        print("Approved dedicated Neon UAT verified; creating first platform administrator", flush=True)
        subprocess.run([sys.executable, "-m", "tools.bootstrap_admin",
                        "--email", email,
                        "--display-name", "UAT Administrator",
                        "--use-configured-database",
                        "--password-env", "BOOTSTRAP_ADMIN_PASSWORD"], env=env, check=True)
        print("UAT ADMIN BOOTSTRAP PASS", flush=True)
        return 0
    except Exception:
        print("UAT ADMIN BOOTSTRAP STOPPED; no credentials exposed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
