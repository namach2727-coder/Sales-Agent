from __future__ import annotations

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.authentication.service import normalize_email
from app.config import get_settings
from app.models import CommerceAuditLog, SaasPlan, TenantMembership, TenantSubscription, UserIdentity
from tools.seed_data import _assert_schema_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Cancel one customer's active purchased plan in UAT only"
    )
    result.add_argument("--email", required=True)
    result.add_argument("--plan-code", required=True)
    result.add_argument("--use-configured-database", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = get_settings()
    if settings.app_env != "uat":
        print("ERROR customer-plan reset is allowed only in UAT")
        return 2
    if not args.use_configured_database:
        print("ERROR explicit --use-configured-database is required")
        return 2

    engine = None
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        _assert_schema_ready(engine)
        normalized = normalize_email(args.email)

        with Session(engine) as session, session.begin():
            user = session.scalar(
                select(UserIdentity).where(UserIdentity.normalized_email == normalized)
            )
            if user is None:
                raise ValueError("target identity not found")

            tenant_ids = tuple(
                session.scalars(
                    select(TenantMembership.tenant_id).where(
                        TenantMembership.user_id == user.id,
                        TenantMembership.status == "active",
                    )
                ).all()
            )
            if not tenant_ids:
                raise ValueError("target identity has no active tenant membership")

            subscriptions = list(
                session.scalars(
                    select(TenantSubscription)
                    .join(SaasPlan, SaasPlan.id == TenantSubscription.plan_id)
                    .where(
                        TenantSubscription.tenant_id.in_(tenant_ids),
                        TenantSubscription.status == "active",
                        TenantSubscription.source == "PURCHASED",
                        SaasPlan.code == args.plan_code,
                    )
                    .order_by(TenantSubscription.id.desc())
                    .with_for_update()
                ).all()
            )
            if not subscriptions:
                raise ValueError("no active purchased subscription matched the target plan")

            for subscription in subscriptions:
                subscription.status = "cancelled"
                session.add(
                    CommerceAuditLog(
                        tenant_id=subscription.tenant_id,
                        store_id=subscription.store_id,
                        actor_user_id=None,
                        action="subscription.uat_customer_plan_reset",
                        target_type="tenant_subscription",
                        target_public_id=subscription.public_id,
                        details_json={
                            "plan_code": args.plan_code,
                            "previous_status": "active",
                            "new_status": "cancelled",
                        },
                    )
                )

            cancelled = len(subscriptions)

        print(f"UAT customer plan reset completed: cancelled={cancelled}")
        return 0
    except ValueError as exc:
        print(f"ERROR UAT customer plan reset failed: {exc}")
        return 1
    except Exception:
        print("ERROR UAT customer plan reset failed; sensitive details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
