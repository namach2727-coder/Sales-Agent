"""Cross-platform command for explicit, profile-safe seed execution."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from tools.seeding import (
    SeedExecutionError,
    SeedProfile,
    SeedRunner,
    SeedValidationError,
    default_registry,
)
from tools.migration_policy import load_script_directory


REQUIRED_TABLES = {
    "auth_permissions",
    "auth_roles",
    "auth_role_permissions",
    "module_definitions",
    "seed_history",
    "store_modules",
    "stores",
    "tenant_memberships",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run explicit, idempotent seed data")
    parser.add_argument("--profile", help="production, development, test, or demo")
    parser.add_argument("--tenant", help="explicit tenant/store slug for tenant seeds")
    parser.add_argument(
        "--seed",
        action="append",
        dest="seed_names",
        help="named seed to run; repeat to select multiple seeds",
    )
    parser.add_argument("--dry-run", action="store_true", help="roll back all intended writes")
    parser.add_argument("--list", action="store_true", help="list registered seeds without a database")
    database = parser.add_mutually_exclusive_group()
    database.add_argument("--database-url", help="explicit SQLAlchemy database URL")
    database.add_argument(
        "--use-configured-database",
        action="store_true",
        help="explicitly opt in to DATABASE_URL from application settings",
    )
    return parser


def _list_seeds() -> None:
    for definition in default_registry().definitions():
        profiles = ",".join(sorted(profile.value for profile in definition.compatible_profiles))
        print(
            f"{definition.name} version={definition.version} scope={definition.scope.value} "
            f"profiles={profiles} production_safe={str(definition.production_safe).lower()} "
            f"ownership={definition.ownership.value}"
        )


def _database_url(args: argparse.Namespace) -> str:
    if args.database_url:
        make_url(args.database_url)
        return args.database_url
    if args.use_configured_database:
        return get_settings().database_url
    raise SeedValidationError(
        "execution requires --database-url or explicit --use-configured-database"
    )


def _assert_schema_ready(engine) -> None:
    existing = set(inspect(engine).get_table_names())
    missing = sorted(REQUIRED_TABLES - existing)
    if missing:
        raise SeedValidationError(
            "database schema is not at the required migration head; run alembic upgrade head"
        )
    expected_head = load_script_directory().get_current_head()
    with engine.connect() as connection:
        current_head = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one_or_none()
    if current_head != expected_head:
        raise SeedValidationError(
            "database revision is not the expected migration head; run alembic upgrade head"
        )


def _print_report(report) -> None:
    prefix = "DRY-RUN " if report.dry_run else ""
    for result in report.results:
        tenant = f" tenant={result.tenant_slug}" if result.tenant_slug else ""
        print(
            f"{prefix}{result.seed_name}: {result.status.value}{tenant} "
            f"records(created={result.created}, updated={result.updated}, "
            f"unchanged={result.unchanged}, skipped={result.skipped})"
        )
    counts = report.counts
    print(
        "Seed summary: "
        + " ".join(
            f"{name}={counts[name]}"
            for name in ("created", "updated", "unchanged", "skipped", "failed")
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        _list_seeds()
        return 0
    if not args.profile:
        print("ERROR --profile is required for seed execution")
        return 2
    engine = None
    try:
        profile = SeedProfile.parse(args.profile)
        url = _database_url(args)
        engine = create_engine(url)
        _assert_schema_ready(engine)
        report = SeedRunner(engine, default_registry()).run(
            profile,
            tenant_slug=args.tenant,
            seed_names=tuple(args.seed_names) if args.seed_names else None,
            dry_run=args.dry_run,
        )
        _print_report(report)
        return 0
    except SeedExecutionError as exc:
        print(f"ERROR seed {exc.seed_name!r} failed and was rolled back")
        if exc.report is not None:
            _print_report(exc.report)
        else:
            print("Seed summary: created=0 updated=0 unchanged=0 skipped=0 failed=1")
        return 1
    except SeedValidationError as exc:
        print(f"ERROR {exc}")
        return 2
    except (ImportError, SQLAlchemyError, ValueError):
        print("ERROR database validation or execution failed; credentials were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
