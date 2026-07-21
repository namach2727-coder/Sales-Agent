from __future__ import annotations

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import UserIdentity
from app.tenant_management.domain import TenantManagementError
from app.tenant_management.service import TenantStoreService
from tools.seed_data import _assert_schema_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Atomically bootstrap a tenant, its first store, and an existing verified owner"
    )
    result.add_argument("--tenant-name", required=True)
    result.add_argument("--tenant-slug", required=True)
    result.add_argument("--store-name", required=True)
    result.add_argument("--store-slug", required=True)
    result.add_argument("--owner-email", required=True)
    result.add_argument("--database-url")
    result.add_argument("--use-configured-database", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if bool(args.database_url) == bool(args.use_configured_database):
        print("ERROR select exactly one database source")
        return 2
    url = get_settings().database_url if args.use_configured_database else args.database_url
    engine = None
    try:
        assert url is not None
        make_url(url)
        engine = create_engine(url, pool_pre_ping=True)
        _assert_schema_ready(engine)
        with Session(engine) as session:
            owner = session.scalar(
                select(UserIdentity).where(
                    UserIdentity.normalized_email == args.owner_email.strip().casefold()
                )
            )
            if owner is None:
                raise ValueError("owner identity does not exist")
            tenant, store, membership = TenantStoreService(
                session, actor_identity_id=owner.id
            ).bootstrap(
                tenant_name=args.tenant_name,
                tenant_slug=args.tenant_slug,
                store_name=args.store_name,
                store_slug=args.store_slug,
                owner_identity=owner,
            )
            print(
                "Tenant bootstrap completed: "
                f"tenant_public_id={tenant.public_id} "
                f"store_public_id={store.public_id} membership_id={membership.id}"
            )
        return 0
    except (ValueError, TenantManagementError) as exc:
        print(f"ERROR tenant bootstrap failed: {exc}")
        return 1
    except Exception:
        print("ERROR tenant bootstrap failed; sensitive details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
