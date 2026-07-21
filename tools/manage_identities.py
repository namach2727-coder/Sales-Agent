"""Credential-safe identity and membership administration CLI."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import getpass
import json

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.authentication.exceptions import (
    AuthenticationError,
    IdentityConflict,
    MembershipConflict,
)
from app.authz import AuthorizationPrincipal, AuthorizationService, PrincipalType
from app.config import get_settings
from app.models import AuthSession, Store, TenantMembership, UserIdentity
from app.tenancy import normalize_store_slug
from tools.seed_data import _assert_schema_ready


def _database_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--database-url")
    group.add_argument("--use-configured-database", action="store_true")
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage persistent identities safely")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-user")
    create.add_argument("--email", required=True)
    create.add_argument("--display-name", required=True)
    create.add_argument("--email-verified", action="store_true")
    for name in ("list-users",):
        _database_arguments(commands.add_parser(name))
    for name in ("show-user", "enable-user", "disable-user", "set-password", "revoke-all-sessions", "list-memberships", "show-effective-access"):
        command = commands.add_parser(name)
        command.add_argument("--user-id", required=True, type=int)
        if name == "show-effective-access":
            command.add_argument("--tenant")
        _database_arguments(command)
    for name in ("add-tenant-membership", "disable-tenant-membership"):
        command = commands.add_parser(name)
        command.add_argument("--user-id", required=True, type=int)
        command.add_argument("--tenant", required=True)
        _database_arguments(command)
    revoke = commands.add_parser("revoke-session")
    revoke.add_argument("--session-id", required=True)
    _database_arguments(revoke)
    _database_arguments(create)
    return parser


def _database_url(args: argparse.Namespace) -> str:
    value = get_settings().database_url if args.use_configured_database else args.database_url
    assert value is not None
    make_url(value)
    return value


def _service(session: Session) -> AuthenticationService:
    settings = get_settings()
    return AuthenticationService(
        session,
        password_service=PasswordService(
            minimum_length=settings.password_min_length,
            maximum_length=settings.password_max_length,
        ),
        session_ttl_minutes=settings.session_ttl_minutes,
        login_max_failures=settings.login_max_failures,
        login_lockout_minutes=settings.login_lockout_minutes,
    )


def _tenant_id(session: Session, slug: str) -> int:
    normalized = normalize_store_slug(slug)
    tenant_id = session.scalar(select(Store.id).where(Store.slug == normalized))
    if tenant_id is None:
        raise ValueError("tenant could not be resolved")
    return tenant_id


def _print(value: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
    elif isinstance(value, list):
        for item in value:
            print(" ".join(f"{key}={data}" for key, data in item.items()))
    elif isinstance(value, dict):
        print(" ".join(f"{key}={data}" for key, data in value.items()))
    else:
        print(value)


def _user_dict(user: UserIdentity) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
        "email_verified": user.email_verified,
        "is_service_account": user.is_service_account,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        engine = create_engine(_database_url(args))
        _assert_schema_ready(engine)
        with Session(engine, expire_on_commit=False) as session:
            service = _service(session)
            if args.command == "create-user":
                password = getpass.getpass("Password: ")
                confirmation = getpass.getpass("Confirm password: ")
                if password != confirmation:
                    raise ValueError("password confirmation does not match")
                user = service.create_user(
                    email=args.email,
                    display_name=args.display_name,
                    password=password,
                    email_verified=args.email_verified,
                )
                _print(_user_dict(user), args.json)
            elif args.command == "list-users":
                users = session.scalars(select(UserIdentity).order_by(UserIdentity.id)).all()
                _print([_user_dict(item) for item in users], args.json)
            elif args.command == "show-user":
                user = session.get(UserIdentity, args.user_id)
                if user is None:
                    raise ValueError("identity not found")
                _print(_user_dict(user), args.json)
            elif args.command in ("enable-user", "disable-user"):
                service.set_user_enabled(
                    user_id=args.user_id, enabled=args.command == "enable-user"
                )
                _print({"status": "updated", "user_id": args.user_id}, args.json)
            elif args.command == "set-password":
                password = getpass.getpass("New password: ")
                confirmation = getpass.getpass("Confirm new password: ")
                if password != confirmation:
                    raise ValueError("password confirmation does not match")
                service.set_password(user_id=args.user_id, password=password)
                _print({"status": "password_changed", "user_id": args.user_id}, args.json)
            elif args.command in ("add-tenant-membership", "disable-tenant-membership"):
                tenant_id = _tenant_id(session, args.tenant)
                session.rollback()  # tenant lookup is read-only; mutation service owns a clean transaction.
                if args.command == "add-tenant-membership":
                    service.add_tenant_membership(user_id=args.user_id, tenant_id=tenant_id)
                    status = "active"
                else:
                    service.set_membership_enabled(
                        user_id=args.user_id, tenant_id=tenant_id, enabled=False
                    )
                    status = "disabled"
                _print({"user_id": args.user_id, "tenant_id": tenant_id, "status": status}, args.json)
            elif args.command == "list-memberships":
                rows = session.scalars(
                    select(TenantMembership).where(TenantMembership.user_id == args.user_id)
                ).all()
                _print([
                    {"id": row.id, "tenant_id": row.tenant_id, "status": row.status}
                    for row in rows
                ], args.json)
            elif args.command == "revoke-session":
                auth_session = session.get(AuthSession, args.session_id)
                if auth_session is None:
                    raise ValueError("session not found")
                user_id = auth_session.user_id
                session.rollback()
                service.revoke_session(
                    session_id=args.session_id,
                    actor_user_id=user_id,
                    target_user_id=user_id,
                )
                _print({"session_id": args.session_id, "status": "revoked"}, args.json)
            elif args.command == "revoke-all-sessions":
                count = service.revoke_all_user_sessions(user_id=args.user_id)
                _print({"user_id": args.user_id, "revoked": count}, args.json)
            elif args.command == "show-effective-access":
                tenant_id = _tenant_id(session, args.tenant) if args.tenant else None
                principal = AuthorizationPrincipal(
                    str(args.user_id), PrincipalType.USER, True, tenant_id=tenant_id
                )
                permissions = AuthorizationService(session).effective_permissions(
                    principal, tenant_id=tenant_id
                )
                _print(list(permissions), args.json)
        return 0
    except (IdentityConflict, MembershipConflict):
        print("ERROR identity or membership conflict")
        return 3
    except (ValueError, AuthenticationError) as exc:
        print(f"ERROR {exc}")
        return 2
    except (ImportError, SQLAlchemyError):
        print("ERROR database validation or execution failed; credentials were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
