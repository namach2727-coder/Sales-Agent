from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.authentication.exceptions import AuthenticationError
from app.authentication.service import normalize_email
from app.authz import PrincipalType
from app.config import get_settings
from app.models import AuthPlatformRoleAssignment, IdentityAuditLog, UserIdentity
from tools.seed_data import _assert_schema_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Reset the password of an existing active platform administrator"
    )
    result.add_argument("--email", required=True)
    result.add_argument("--database-url")
    result.add_argument("--use-configured-database", action="store_true")
    result.add_argument(
        "--password-env",
        required=True,
        metavar="VARIABLE",
        help="Read the replacement password from this environment variable.",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if bool(args.database_url) == bool(args.use_configured_database):
        print("ERROR select exactly one database source")
        return 2

    password = os.environ.get(args.password_env)
    if password is None:
        print("ERROR password environment variable is not set")
        return 2

    url = get_settings().database_url if args.use_configured_database else args.database_url
    engine = None
    try:
        assert url is not None
        make_url(url)
        engine = create_engine(url, pool_pre_ping=True)
        _assert_schema_ready(engine)
        normalized = normalize_email(args.email)

        with Session(engine) as session:
            user = session.scalar(
                select(UserIdentity).where(UserIdentity.normalized_email == normalized)
            )
            if user is None:
                raise ValueError("platform administrator identity not found")
            if user.status != "active" or user.is_service_account:
                raise ValueError("platform administrator identity is not active")
            role = session.scalar(
                select(AuthPlatformRoleAssignment.id).where(
                    AuthPlatformRoleAssignment.principal_type == PrincipalType.USER.value,
                    AuthPlatformRoleAssignment.principal_id == str(user.id),
                    AuthPlatformRoleAssignment.role_code == "platform_super_admin",
                    AuthPlatformRoleAssignment.status == "active",
                )
            )
            if role is None:
                raise ValueError("target identity is not an active platform administrator")
            user_id = user.id

        settings = get_settings()
        with Session(engine) as session:
            AuthenticationService(
                session,
                password_service=PasswordService(
                    minimum_length=settings.password_min_length,
                    maximum_length=settings.password_max_length,
                ),
            ).set_password(user_id=user_id, password=password)

        with Session(engine) as session, session.begin():
            session.add(
                IdentityAuditLog(
                    event_code="bootstrap.platform_admin_password_reset",
                    target_user_id=user_id,
                    outcome="succeeded",
                )
            )

        print(f"Platform administrator password reset: user_id={user_id}")
        return 0
    except (ValueError, AuthenticationError) as exc:
        print(f"ERROR platform administrator password reset failed: {exc}")
        return 1
    except Exception:
        print("ERROR platform administrator password reset failed; sensitive details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
