"""Add production tenant and multi-store management boundaries.

Revision ID: 0005_tenant_store_management
Revises: 0004_authentication_identity
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "0005_tenant_store_management"
down_revision: str | None = "0004_authentication_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMING = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}
FK_NAMING = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}


def _replace_tenant_fk(table: str, nullable: bool) -> None:
    with op.batch_alter_table(table, recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_constraint(f"fk_{table}_tenant_id_stores", type_="foreignkey")
        batch.create_foreign_key(
            f"fk_{table}_tenant_id_tenants",
            "tenants",
            ["tenant_id"],
            ["id"],
        )


def _restore_store_fk(table: str) -> None:
    with op.batch_alter_table(table, recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_constraint(f"fk_{table}_tenant_id_tenants", type_="foreignkey")
        batch.create_foreign_key(
            f"fk_{table}_tenant_id_stores",
            "stores",
            ["tenant_id"],
            ["id"],
        )


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by_identity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'archived')",
            name="ck_tenants_status",
        ),
        sa.ForeignKeyConstraint(
            ("created_by_identity_id",), ("user_identities.id",)
        ),
    )
    op.create_index("ix_tenants_public_id", "tenants", ["public_id"], unique=True)
    op.create_index("ix_tenants_slug_lower", "tenants", ["slug"], unique=True)
    op.create_index("ix_tenants_status", "tenants", ["status"])
    op.create_index(
        "ix_tenants_created_by_identity_id", "tenants", ["created_by_identity_id"]
    )

    connection = op.get_bind()
    stores = list(
        connection.execute(
            sa.text("SELECT id, name, slug, status, created_at, updated_at FROM stores ORDER BY id")
        ).mappings()
    )
    now = datetime.now(UTC)
    tenant_table = sa.table(
        "tenants",
        sa.column("id", sa.Integer()),
        sa.column("public_id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    for store in stores:
        status = (
            "archived"
            if store["status"] in {"deleted", "archived"}
            else "suspended"
            if store["status"] in {"disabled", "suspended"}
            else "active"
        )
        connection.execute(
            tenant_table.insert().values(
                id=store["id"],
                public_id=str(uuid.uuid4()),
                name=store["name"],
                slug=str(store["slug"]).lower(),
                status=status,
                created_at=store["created_at"] or now,
                updated_at=store["updated_at"] or now,
            )
        )

    with op.batch_alter_table("stores", recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_index("ix_stores_slug")
        batch.add_column(sa.Column("public_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("timezone", sa.String(64), nullable=True))
        batch.add_column(sa.Column("locale", sa.String(16), nullable=True))
        batch.add_column(sa.Column("currency_code", sa.String(3), nullable=True))
        batch.add_column(sa.Column("subdomain", sa.String(63), nullable=True))
        batch.add_column(sa.Column("custom_domain", sa.String(255), nullable=True))
        batch.add_column(sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch.alter_column("slug", type_=sa.String(63), existing_nullable=False)

    for store in stores:
        connection.execute(
            sa.text(
                "UPDATE stores SET public_id=:public_id, tenant_id=:tenant_id, "
                "timezone='Asia/Tehran', locale='fa-IR', currency_code='IRR', "
                "subdomain=lower(slug) WHERE id=:store_id"
            ),
            {
                "public_id": str(uuid.uuid4()),
                "tenant_id": store["id"],
                "store_id": store["id"],
            },
        )

    with op.batch_alter_table("stores", recreate="always", naming_convention=FK_NAMING) as batch:
        batch.alter_column("public_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("tenant_id", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("timezone", existing_type=sa.String(64), nullable=False)
        batch.alter_column("locale", existing_type=sa.String(16), nullable=False)
        batch.alter_column("currency_code", existing_type=sa.String(3), nullable=False)

        batch.create_foreign_key("fk_stores_tenant_id_tenants", "tenants", ["tenant_id"], ["id"])
        batch.create_unique_constraint("uq_stores_tenant_slug", ["tenant_id", "slug"])
        batch.create_unique_constraint("uq_stores_subdomain", ["subdomain"])
        batch.create_unique_constraint("uq_stores_custom_domain", ["custom_domain"])
        batch.create_check_constraint(
            "ck_stores_status",
            "status IN ('active', 'suspended', 'archived', 'onboarding', 'provisioning', 'disabled', 'deleted')",
        )
        batch.create_index("ix_stores_public_id", ["public_id"], unique=True)
        batch.create_index("ix_stores_tenant_id", ["tenant_id"])
        batch.create_index("ix_stores_slug", ["slug"])

    op.add_column(
        "tenant_memberships", sa.Column("public_id", sa.String(36), nullable=True)
    )
    membership_ids = list(
        connection.execute(sa.text("SELECT id FROM tenant_memberships")).scalars()
    )
    for membership_id in membership_ids:
        connection.execute(
            sa.text(
                "UPDATE tenant_memberships SET public_id=:public_id WHERE id=:membership_id"
            ),
            {"public_id": str(uuid.uuid4()), "membership_id": membership_id},
        )

    with op.batch_alter_table("tenant_memberships", recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_constraint("ck_tenant_memberships_status", type_="check")
        batch.add_column(sa.Column("all_store_access", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint(
            "ck_tenant_memberships_status",
            "status IN ('invited', 'active', 'suspended', 'revoked', 'disabled')",
        )
        batch.drop_constraint("fk_tenant_memberships_tenant_id_stores", type_="foreignkey")
        batch.create_foreign_key(
            "fk_tenant_memberships_tenant_id_tenants", "tenants", ["tenant_id"], ["id"]
        )
        batch.alter_column(
            "public_id", existing_type=sa.String(36), nullable=False
        )
        batch.create_index(
            "ix_tenant_memberships_public_id", ["public_id"], unique=True
        )
        batch.alter_column(
            "all_store_access",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )

    for table in ("seed_history", "identity_audit_logs", "auth_audit_logs"):
        _replace_tenant_fk(table, nullable=True)

    op.create_table(
        "store_access_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by_identity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'revoked')",
            name="ck_store_access_status",
        ),
        sa.ForeignKeyConstraint(("membership_id",), ("tenant_memberships.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.ForeignKeyConstraint(("created_by_identity_id",), ("user_identities.id",)),
        sa.UniqueConstraint(
            "membership_id", "store_id", name="uq_store_access_membership_store"
        ),
    )
    for column in ("membership_id", "store_id", "status"):
        op.create_index(
            f"ix_store_access_assignments_{column}", "store_access_assignments", [column]
        )

    op.create_table(
        "tenant_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("actor_identity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_public_id", sa.String(100), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("tenant_id",), ("tenants.id",)),
        sa.ForeignKeyConstraint(("store_id",), ("stores.id",)),
        sa.ForeignKeyConstraint(("actor_identity_id",), ("user_identities.id",)),
    )
    for column in ("tenant_id", "store_id", "actor_identity_id", "action", "created_at"):
        op.create_index(f"ix_tenant_audit_logs_{column}", "tenant_audit_logs", [column])


def downgrade() -> None:
    op.drop_table("tenant_audit_logs")
    op.drop_table("store_access_assignments")
    for table in ("auth_audit_logs", "identity_audit_logs", "seed_history"):
        _restore_store_fk(table)
    op.execute("UPDATE tenant_memberships SET status='disabled' WHERE status != 'active'")
    with op.batch_alter_table("tenant_memberships", recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_index("ix_tenant_memberships_public_id")
        batch.drop_constraint("ck_tenant_memberships_status", type_="check")
        batch.drop_constraint("fk_tenant_memberships_tenant_id_tenants", type_="foreignkey")
        batch.create_foreign_key(
            "fk_tenant_memberships_tenant_id_stores", "stores", ["tenant_id"], ["id"]
        )
        batch.create_check_constraint(
            "ck_tenant_memberships_status", "status IN ('active', 'disabled')"
        )
        for column in (
            "revoked_at", "suspended_at", "activated_at", "invited_at",
            "all_store_access", "public_id",
        ):
            batch.drop_column(column)
    with op.batch_alter_table("stores", recreate="always", naming_convention=FK_NAMING) as batch:
        batch.drop_index("ix_stores_public_id")
        batch.drop_index("ix_stores_tenant_id")
        batch.drop_index("ix_stores_slug")
        batch.drop_constraint("ck_stores_status", type_="check")
        batch.drop_constraint("uq_stores_custom_domain", type_="unique")
        batch.drop_constraint("uq_stores_subdomain", type_="unique")
        batch.drop_constraint("uq_stores_tenant_slug", type_="unique")
        batch.drop_constraint("fk_stores_tenant_id_tenants", type_="foreignkey")
        batch.alter_column("slug", type_=sa.String(100), existing_nullable=False)
        for column in (
            "deleted_at", "archived_at", "suspended_at", "custom_domain", "subdomain",
            "currency_code", "locale", "timezone", "tenant_id", "public_id",
        ):
            batch.drop_column(column)
        batch.create_index("ix_stores_slug", ["slug"], unique=True)
    op.drop_table("tenants")
