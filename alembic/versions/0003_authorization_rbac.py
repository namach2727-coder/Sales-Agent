"""Create normalized platform and tenant RBAC tables."""

from alembic import op
import sqlalchemy as sa


revision = "0003_authorization_rbac"
down_revision = "0002_create_seed_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_permissions",
        sa.Column("code", sa.String(100), primary_key=True, nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("system_managed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_permissions_scope", "auth_permissions", ["scope"])
    op.create_table(
        "auth_roles",
        sa.Column("code", sa.String(100), primary_key=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("system_managed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_roles_scope", "auth_roles", ["scope"])
    op.create_table(
        "auth_role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("role_code", sa.String(100), nullable=False),
        sa.Column("permission_code", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("role_code",), ("auth_roles.code",)),
        sa.ForeignKeyConstraint(("permission_code",), ("auth_permissions.code",)),
        sa.UniqueConstraint("role_code", "permission_code", name="uq_auth_role_permission"),
    )
    op.create_index("ix_auth_role_permissions_role_code", "auth_role_permissions", ["role_code"])
    op.create_index("ix_auth_role_permissions_permission_code", "auth_role_permissions", ["permission_code"])
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("principal_type", sa.String(30), nullable=False),
        sa.Column("principal_id", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("tenant_id",), ("stores.id",)),
        sa.UniqueConstraint("tenant_id", "principal_type", "principal_id", name="uq_tenant_membership_principal"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index("ix_tenant_memberships_principal_id", "tenant_memberships", ["principal_id"])
    op.create_index("ix_tenant_memberships_status", "tenant_memberships", ["status"])
    op.create_table(
        "auth_platform_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("principal_type", sa.String(30), nullable=False),
        sa.Column("principal_id", sa.String(200), nullable=False),
        sa.Column("role_code", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("role_code",), ("auth_roles.code",)),
        sa.UniqueConstraint("principal_type", "principal_id", "role_code", name="uq_auth_platform_principal_role"),
    )
    op.create_index("ix_auth_platform_role_assignments_principal_id", "auth_platform_role_assignments", ["principal_id"])
    op.create_index("ix_auth_platform_role_assignments_role_code", "auth_platform_role_assignments", ["role_code"])
    op.create_index("ix_auth_platform_role_assignments_status", "auth_platform_role_assignments", ["status"])
    op.create_table(
        "auth_tenant_role_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("role_code", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("membership_id",), ("tenant_memberships.id",)),
        sa.ForeignKeyConstraint(("role_code",), ("auth_roles.code",)),
        sa.UniqueConstraint("membership_id", "role_code", name="uq_auth_tenant_membership_role"),
    )
    op.create_index("ix_auth_tenant_role_assignments_membership_id", "auth_tenant_role_assignments", ["membership_id"])
    op.create_index("ix_auth_tenant_role_assignments_role_code", "auth_tenant_role_assignments", ["role_code"])
    op.create_index("ix_auth_tenant_role_assignments_status", "auth_tenant_role_assignments", ["status"])
    op.create_table(
        "auth_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("actor_principal_type", sa.String(30), nullable=False),
        sa.Column("actor_principal_id", sa.String(200), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_principal_type", sa.String(30), nullable=False),
        sa.Column("target_principal_id", sa.String(200), nullable=False),
        sa.Column("target_role_code", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("tenant_id",), ("stores.id",)),
    )
    op.create_index("ix_auth_audit_logs_tenant_id", "auth_audit_logs", ["tenant_id"])
    op.create_index("ix_auth_audit_logs_actor_principal_id", "auth_audit_logs", ["actor_principal_id"])
    op.create_index("ix_auth_audit_logs_action", "auth_audit_logs", ["action"])
    op.create_index("ix_auth_audit_logs_created_at", "auth_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("auth_audit_logs")
    op.drop_table("auth_tenant_role_assignments")
    op.drop_table("auth_platform_role_assignments")
    op.drop_table("tenant_memberships")
    op.drop_table("auth_role_permissions")
    op.drop_table("auth_roles")
    op.drop_table("auth_permissions")
