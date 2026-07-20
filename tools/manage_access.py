"""Safe cross-platform administration for RBAC assignments."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.authz import (
    AccessConflictError,
    AccessManagementError,
    AccessValidationError,
    AuthorizationPrincipal,
    AuthorizationService,
    PrincipalType,
    RoleAssignmentService,
)
from app.authz.dependencies import local_provider_admin_principal
from app.models import AuthPermission, AuthRole, Store
from app.tenancy import normalize_store_slug
from app.config import get_settings
from tools.seed_data import _assert_schema_ready


COMMANDS = (
    "list-permissions",
    "list-roles",
    "show-effective-permissions",
    "assign-role",
    "revoke-role",
)


def _add_database_arguments(parser: argparse.ArgumentParser) -> None:
    database = parser.add_mutually_exclusive_group(required=True)
    database.add_argument("--database-url", help="explicit SQLAlchemy database URL")
    database.add_argument(
        "--use-configured-database",
        action="store_true",
        help="explicitly opt in to configured DATABASE_URL",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")


def _add_principal_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--principal-type", required=True)
    parser.add_argument("--principal-id", required=True)
    parser.add_argument("--tenant", help="explicit tenant slug for tenant-scoped access")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage explicit RBAC assignments")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list-permissions", "list-roles"):
        command = subparsers.add_parser(name)
        _add_database_arguments(command)
    effective = subparsers.add_parser("show-effective-permissions")
    _add_principal_arguments(effective)
    _add_database_arguments(effective)
    for name in ("assign-role", "revoke-role"):
        command = subparsers.add_parser(name)
        _add_principal_arguments(command)
        command.add_argument("--role", required=True)
        _add_database_arguments(command)
    return parser


def _database_url(args: argparse.Namespace) -> str:
    url = get_settings().database_url if args.use_configured_database else args.database_url
    assert url is not None
    make_url(url)
    return url


def _tenant_id(engine, slug: str | None) -> int | None:
    if slug is None:
        return None
    try:
        normalized = normalize_store_slug(slug)
    except ValueError as exc:
        raise AccessValidationError("invalid tenant slug") from exc
    with Session(engine) as session:
        tenant_id = session.scalar(select(Store.id).where(Store.slug == normalized))
    if tenant_id is None:
        raise AccessValidationError("tenant could not be resolved")
    return tenant_id


def _print(data: object, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, sort_keys=True))
        return
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                print(" ".join(f"{key}={value}" for key, value in item.items()))
            else:
                print(item)
    elif isinstance(data, dict):
        print(" ".join(f"{key}={value}" for key, value in data.items()))
    else:
        print(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        engine = create_engine(_database_url(args))
        _assert_schema_ready(engine)
        if args.command == "list-permissions":
            with Session(engine) as session:
                data = [
                    {"code": item.code, "scope": item.scope, "description": item.description}
                    for item in session.scalars(select(AuthPermission).order_by(AuthPermission.code))
                ]
            _print(data, as_json=args.json)
            return 0
        if args.command == "list-roles":
            with Session(engine) as session:
                data = [
                    {"code": item.code, "scope": item.scope, "name": item.display_name}
                    for item in session.scalars(select(AuthRole).order_by(AuthRole.code))
                ]
            _print(data, as_json=args.json)
            return 0

        principal_type = PrincipalType.parse(args.principal_type)
        principal_id = args.principal_id.strip()
        if not principal_id or principal_type is PrincipalType.ANONYMOUS:
            raise AccessValidationError("a stable non-anonymous principal is required")
        tenant_id = _tenant_id(engine, args.tenant)
        principal = AuthorizationPrincipal(
            subject_id=principal_id,
            subject_type=principal_type,
            authenticated=True,
            tenant_id=tenant_id,
        )
        if args.command == "show-effective-permissions":
            with Session(engine) as session:
                permissions = AuthorizationService(session).effective_permissions(
                    principal, tenant_id=tenant_id
                )
            _print(list(permissions), as_json=args.json)
            return 0

        with Session(engine, expire_on_commit=False) as session:
            service = RoleAssignmentService(
                session,
                actor=local_provider_admin_principal(),
            )
            operation = (
                service.assign_role
                if args.command == "assign-role"
                else service.revoke_role
            )
            result = operation(
                principal_type=principal_type,
                principal_id=principal_id,
                role_code=args.role,
                tenant_id=tenant_id,
            )
        _print(
            {
                "principal_type": result.principal_type,
                "principal_id": result.principal_id,
                "role": result.role_code,
                "tenant_id": result.tenant_id,
                "status": result.status,
                "changed": result.changed,
            },
            as_json=args.json,
        )
        return 0
    except (AccessValidationError, ValueError) as exc:
        print(f"ERROR {exc}")
        return 2
    except AccessConflictError as exc:
        print(f"ERROR {exc}")
        return 3
    except AccessManagementError:
        print("ERROR access management failed and was rolled back")
        return 1
    except (ImportError, SQLAlchemyError):
        print("ERROR database validation or execution failed; credentials were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
