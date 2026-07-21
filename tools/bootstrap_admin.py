from __future__ import annotations

import argparse
import getpass
import os

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.authentication.exceptions import AuthenticationError
from app.authz import PrincipalType, RoleAssignmentService
from app.authz.dependencies import local_provider_admin_principal
from app.authz.exceptions import AccessManagementError
from app.config import get_settings
from app.models import AuthPlatformRoleAssignment, IdentityAuditLog
from tools.seed_data import _assert_schema_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Create the first explicit platform administrator")
    result.add_argument("--email", required=True)
    result.add_argument("--display-name", required=True)
    result.add_argument("--database-url")
    result.add_argument("--use-configured-database", action="store_true")
    result.add_argument(
        "--password-env",
        metavar="VARIABLE",
        help="Read the password from this environment variable instead of prompting.",
    )
    return result


def _password(args: argparse.Namespace) -> str:
    if args.password_env:
        value = os.environ.get(args.password_env)
        if value is None:
            raise ValueError("password environment variable is not set")
        return value
    first = getpass.getpass("Platform administrator password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        raise ValueError("password confirmation does not match")
    return first


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if bool(args.database_url) == bool(args.use_configured_database):
        print("ERROR select exactly one database source")
        return 2
    url = get_settings().database_url if args.use_configured_database else args.database_url
    engine = None
    created_user_id: int | None = None
    try:
        assert url is not None
        make_url(url)
        password = _password(args)
        engine = create_engine(url, pool_pre_ping=True)
        _assert_schema_ready(engine)
        with Session(engine) as session:
            existing = session.scalar(
                select(AuthPlatformRoleAssignment.id).where(
                    AuthPlatformRoleAssignment.role_code == "platform_super_admin",
                    AuthPlatformRoleAssignment.status == "active",
                )
            )
            if existing is not None:
                raise ValueError("an active platform administrator already exists")
        settings = get_settings()
        with Session(engine, expire_on_commit=False) as session:
            user = AuthenticationService(
                session,
                password_service=PasswordService(
                    minimum_length=settings.password_min_length,
                    maximum_length=settings.password_max_length,
                ),
            ).create_user(
                email=args.email,
                display_name=args.display_name,
                password=password,
                email_verified=True,
            )
            created_user_id = user.id
        with Session(engine) as session:
            RoleAssignmentService(session, local_provider_admin_principal()).assign_role(
                principal_type=PrincipalType.USER,
                principal_id=str(created_user_id),
                role_code="platform_super_admin",
            )
        with Session(engine) as session, session.begin():
            session.add(
                IdentityAuditLog(
                    event_code="bootstrap.platform_admin_created",
                    target_user_id=created_user_id,
                    outcome="succeeded",
                )
            )
        print(f"Platform administrator created: user_id={created_user_id}")
        return 0
    except (ValueError, AuthenticationError, AccessManagementError) as exc:
        if engine is not None and created_user_id is not None:
            try:
                with Session(engine) as session:
                    AuthenticationService(session).set_user_enabled(
                        user_id=created_user_id,
                        enabled=False,
                    )
            except Exception:
                pass
        print(f"ERROR platform administrator bootstrap failed: {exc}")
        return 1
    except Exception:
        print("ERROR platform administrator bootstrap failed; sensitive details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
