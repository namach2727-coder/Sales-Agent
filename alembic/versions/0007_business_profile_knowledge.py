"""business profile and knowledge

Revision ID: 0007_business_profile_knowledge
Revises: 0006_lean_business_catalog
Create Date: 2026-07-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0007_business_profile_knowledge"
down_revision: Union[str, Sequence[str], None] = "0006_lean_business_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESTRUCTIVE_MIGRATION_ACKNOWLEDGED = False
EMPTY_DOWNGRADE_ALLOWED = False


STATUS_CHECK = "status IN ('draft', 'published', 'archived')"
TIMESTAMP_STATE_CHECK = (
    "(status = 'draft' AND published_at IS NULL AND archived_at IS NULL) OR "
    "(status = 'published' AND published_at IS NOT NULL AND archived_at IS NULL) OR "
    "(status = 'archived' AND published_at IS NULL AND archived_at IS NOT NULL)"
)


def upgrade() -> None:
    op.create_table(
        "business_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("business_category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("support_phone", sa.String(length=32), nullable=True),
        sa.Column("support_email", sa.String(length=320), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("address_text", sa.Text(), nullable=True),
        sa.Column("working_hours_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(STATUS_CHECK, name="ck_business_profiles_status"),
        sa.CheckConstraint(
            "revision >= 1", name="ck_business_profiles_revision"
        ),
        sa.CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_profiles_timestamp_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_business_profiles_store_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "tenant_id", name="uq_business_profiles_id_tenant"
        ),
        sa.UniqueConstraint("store_id", name="uq_business_profiles_store"),
    )
    op.create_index(
        op.f("ix_business_profiles_public_id"),
        "business_profiles",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_business_profiles_tenant_id"),
        "business_profiles",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_profiles_store_id"),
        "business_profiles",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_profiles_status"),
        "business_profiles",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_business_profiles_tenant_store_status",
        "business_profiles",
        ["tenant_id", "store_id", "status"],
        unique=False,
    )

    op.create_table(
        "business_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("policy_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(STATUS_CHECK, name="ck_business_policies_status"),
        sa.CheckConstraint(
            "revision >= 1", name="ck_business_policies_revision"
        ),
        sa.CheckConstraint(
            "priority >= 0", name="ck_business_policies_priority"
        ),
        sa.CheckConstraint(
            "policy_type IN ('shipping', 'returns', 'refunds', 'payment', "
            "'warranty', 'service', 'privacy', 'custom')",
            name="ck_business_policies_policy_type",
        ),
        sa.CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_policies_timestamp_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_business_policies_store_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "tenant_id", name="uq_business_policies_id_tenant"
        ),
        sa.UniqueConstraint(
            "store_id", "code", name="uq_business_policies_store_code"
        ),
    )
    op.create_index(
        op.f("ix_business_policies_public_id"),
        "business_policies",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_business_policies_tenant_id"),
        "business_policies",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_policies_store_id"),
        "business_policies",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_policies_policy_type"),
        "business_policies",
        ["policy_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_policies_status"),
        "business_policies",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_business_policies_tenant_store_status",
        "business_policies",
        ["tenant_id", "store_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_business_policies_tenant_store_type",
        "business_policies",
        ["tenant_id", "store_id", "policy_type"],
        unique=False,
    )

    op.create_table(
        "business_faqs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.String(length=500), nullable=False),
        sa.Column("normalized_question", sa.String(length=500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(STATUS_CHECK, name="ck_business_faqs_status"),
        sa.CheckConstraint("revision >= 1", name="ck_business_faqs_revision"),
        sa.CheckConstraint("priority >= 0", name="ck_business_faqs_priority"),
        sa.CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_faqs_timestamp_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_business_faqs_store_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id", "tenant_id", name="uq_business_faqs_id_tenant"
        ),
        sa.UniqueConstraint(
            "store_id",
            "normalized_question",
            name="uq_business_faqs_store_question",
        ),
    )
    op.create_index(
        op.f("ix_business_faqs_public_id"),
        "business_faqs",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_business_faqs_tenant_id"),
        "business_faqs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_faqs_store_id"),
        "business_faqs",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_faqs_status"),
        "business_faqs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_business_faqs_tenant_store_status",
        "business_faqs",
        ["tenant_id", "store_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_business_faqs_tenant_store_question",
        "business_faqs",
        ["tenant_id", "store_id", "normalized_question"],
        unique=False,
    )

    op.create_table(
        "business_knowledge_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("entry_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            STATUS_CHECK, name="ck_business_knowledge_entries_status"
        ),
        sa.CheckConstraint(
            "revision >= 1", name="ck_business_knowledge_entries_revision"
        ),
        sa.CheckConstraint(
            "priority >= 0", name="ck_business_knowledge_entries_priority"
        ),
        sa.CheckConstraint(
            "entry_type IN ('fact', 'instruction', 'reference', 'custom')",
            name="ck_business_knowledge_entries_entry_type",
        ),
        sa.CheckConstraint(
            TIMESTAMP_STATE_CHECK,
            name="ck_business_knowledge_entries_timestamp_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(
            ["store_id", "tenant_id"],
            ["stores.id", "stores.tenant_id"],
            name="fk_business_knowledge_entries_store_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "id",
            "tenant_id",
            name="uq_business_knowledge_entries_id_tenant",
        ),
        sa.UniqueConstraint(
            "store_id",
            "slug",
            name="uq_business_knowledge_entries_store_slug",
        ),
    )
    op.create_index(
        op.f("ix_business_knowledge_entries_public_id"),
        "business_knowledge_entries",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_business_knowledge_entries_tenant_id"),
        "business_knowledge_entries",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_knowledge_entries_store_id"),
        "business_knowledge_entries",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_knowledge_entries_entry_type"),
        "business_knowledge_entries",
        ["entry_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_business_knowledge_entries_status"),
        "business_knowledge_entries",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_business_knowledge_entries_tenant_store_status",
        "business_knowledge_entries",
        ["tenant_id", "store_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_business_knowledge_entries_tenant_store_type",
        "business_knowledge_entries",
        ["tenant_id", "store_id", "entry_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("business_knowledge_entries")
    op.drop_table("business_faqs")
    op.drop_table("business_policies")
    op.drop_table("business_profiles")
