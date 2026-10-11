from __future__ import annotations

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.authentication.service import normalize_email
from app.commerce.service import CommerceService
from app.config import get_settings
from app.models import (
    AuthPlatformRoleAssignment,
    ManualPayment,
    SaasPlan,
    SubscriptionOrder,
    TenantSubscription,
    UserIdentity,
)
from tools.seed_data import _assert_schema_ready


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Approve exactly one submitted manual UAT payment for a customer"
    )
    result.add_argument("--email", required=True)
    result.add_argument("--plan-code", required=True)
    result.add_argument("--use-configured-database", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = get_settings()
    if settings.app_env != "uat":
        print("ERROR UAT payment approval is allowed only in UAT")
        return 2
    if not args.use_configured_database:
        print("ERROR explicit --use-configured-database is required")
        return 2

    engine = None
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        _assert_schema_ready(engine)
        normalized = normalize_email(args.email)

        with Session(engine) as session:
            user = session.scalar(
                select(UserIdentity).where(UserIdentity.normalized_email == normalized)
            )
            if user is None:
                raise ValueError("target identity not found")

            rows = list(
                session.execute(
                    select(ManualPayment, SubscriptionOrder, SaasPlan)
                    .join(SubscriptionOrder, SubscriptionOrder.id == ManualPayment.order_id)
                    .join(SaasPlan, SaasPlan.id == SubscriptionOrder.plan_id)
                    .where(
                        ManualPayment.user_id == user.id,
                        ManualPayment.provider == "manual_card_transfer",
                        ManualPayment.status == "submitted",
                        ManualPayment.receipt_storage_key.is_not(None),
                        SubscriptionOrder.status == "payment_submitted",
                        SaasPlan.code == args.plan_code,
                    )
                    .order_by(ManualPayment.submitted_at.desc(), ManualPayment.id.desc())
                ).all()
            )
            if len(rows) != 1:
                raise ValueError(
                    f"expected exactly one submitted payment, found {len(rows)}"
                )

            payment, order, plan = rows[0]
            if payment.amount != order.price_amount or payment.currency != order.currency:
                raise ValueError("payment/order amount mismatch")

            admin_role = session.scalar(
                select(AuthPlatformRoleAssignment)
                .where(
                    AuthPlatformRoleAssignment.principal_type == "user",
                    AuthPlatformRoleAssignment.role_code == "platform_super_admin",
                    AuthPlatformRoleAssignment.status == "active",
                )
                .order_by(AuthPlatformRoleAssignment.id)
            )
            if admin_role is None:
                raise ValueError("active platform super admin not found")
            try:
                actor_user_id = int(admin_role.principal_id)
            except ValueError as exc:
                raise ValueError("platform super admin principal is invalid") from exc

            safe_payment_id = payment.public_id
            expected_revision = payment.revision
            safe_order_id = order.public_id

        with Session(engine) as session:
            approved = CommerceService(session).approve(
                safe_payment_id,
                expected_revision=expected_revision,
                actor_user_id=actor_user_id,
            )

        with Session(engine) as session:
            approved = session.scalar(
                select(ManualPayment).where(ManualPayment.public_id == safe_payment_id)
            )
            order = session.scalar(
                select(SubscriptionOrder).where(SubscriptionOrder.public_id == safe_order_id)
            )
            subscription = session.scalar(
                select(TenantSubscription)
                .where(
                    TenantSubscription.payment_id == approved.id if approved else False,
                    TenantSubscription.status == "active",
                    TenantSubscription.source == "PURCHASED",
                )
                .order_by(TenantSubscription.id.desc())
            ) if approved is not None else None
            if (
                approved is None
                or approved.status != "approved"
                or order is None
                or order.status != "paid"
                or subscription is None
            ):
                raise ValueError("post-approval verification failed")

            print(
                "UAT manual payment approval completed: "
                f"payment_status={approved.status} "
                f"order_status={order.status} "
                f"subscription_status={subscription.status} "
                f"source={subscription.source} "
                f"automation_limit={subscription.limits_json.get('automation_limit', 0)} "
                f"instagram_account_limit={subscription.limits_json.get('instagram_account_limit', 0)} "
                f"duration_days={subscription.limits_json.get('duration_days', 0)}"
            )
        return 0
    except ValueError as exc:
        print(f"ERROR UAT manual payment approval failed: {exc}")
        return 1
    except Exception:
        print("ERROR UAT manual payment approval failed; sensitive details were redacted")
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
