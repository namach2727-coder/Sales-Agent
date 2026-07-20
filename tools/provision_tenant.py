"""Cross-platform CLI for explicit tenant provisioning."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.provisioning import (
    ProvisioningConflictError,
    ProvisioningError,
    ProvisioningValidationError,
    TenantProvisioningRequest,
    TenantProvisioningService,
)
from tools.seed_data import _assert_schema_ready


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision one tenant and its required defaults atomically"
    )
    parser.add_argument("--name", required=True, help="tenant display name")
    parser.add_argument("--slug", required=True, help="canonical tenant subdomain slug")
    parser.add_argument(
        "--profile",
        required=True,
        help="production, development, test, or demo",
    )
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="module code to activate; repeat for multiple modules",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate and roll back")
    parser.add_argument("--json", action="store_true", help="emit a JSON result")
    database = parser.add_mutually_exclusive_group(required=True)
    database.add_argument("--database-url", help="explicit SQLAlchemy database URL")
    database.add_argument(
        "--use-configured-database",
        action="store_true",
        help="explicitly opt in to DATABASE_URL from application settings",
    )
    return parser


def _database_url(args: argparse.Namespace) -> str:
    url = get_settings().database_url if args.use_configured_database else args.database_url
    assert url is not None
    make_url(url)
    return url


def _payload(result) -> dict[str, object]:
    return {
        "operation_id": result.operation_id,
        "status": result.status.value,
        "dry_run": result.dry_run,
        "tenant": {
            "id": result.tenant_id,
            "name": result.tenant_name,
            "slug": result.tenant_slug,
            "status": result.tenant_status,
        },
        "profile": result.profile,
        "completed_steps": list(result.completed_steps),
        "seeds": list(result.seed_names),
        "modules": list(result.module_codes),
    }


def _print_result(result, *, as_json: bool) -> None:
    payload = _payload(result)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    prefix = "DRY-RUN " if result.dry_run else ""
    print(
        f"{prefix}tenant provisioning {result.status.value}: "
        f"slug={result.tenant_slug} profile={result.profile}"
    )
    print(f"Planned steps: {', '.join(result.completed_steps)}")
    print(f"Planned seeds: {', '.join(result.seed_names)}")
    print(
        "Planned active modules: "
        + (", ".join(result.module_codes) if result.module_codes else "none")
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        url = _database_url(args)
        engine = create_engine(url)
        _assert_schema_ready(engine)
        with Session(engine, expire_on_commit=False) as session:
            result = TenantProvisioningService(session).provision(
                TenantProvisioningRequest(
                    name=args.name,
                    slug=args.slug,
                    profile=args.profile,
                    requested_module_codes=tuple(args.modules or ()),
                ),
                dry_run=args.dry_run,
            )
        _print_result(result, as_json=args.json)
        return 0
    except ProvisioningConflictError as exc:
        print(f"ERROR {exc}")
        return 3
    except ProvisioningValidationError as exc:
        print(f"ERROR {exc}")
        return 2
    except ProvisioningError:
        print("ERROR tenant provisioning failed and was rolled back")
        return 1
    except (ImportError, SQLAlchemyError, ValueError):
        print("ERROR database validation or execution failed; credentials were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
