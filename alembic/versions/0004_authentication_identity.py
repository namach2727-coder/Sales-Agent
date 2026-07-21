"""Create persistent identities, opaque sessions, and security audit."""

from alembic import op
import sqlalchemy as sa


revision = "0004_authentication_identity"
down_revision = "0003_authorization_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_identities",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("normalized_email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("is_service_account", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')", name="ck_user_identities_status"
        ),
    )
    op.create_index("ix_user_identities_normalized_email", "user_identities", ["normalized_email"], unique=True)
    op.create_index("ix_user_identities_status", "user_identities", ["status"])
    op.create_index("ix_user_identities_locked_until", "user_identities", ["locked_until"])

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent_hash", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(("user_id",), ("user_identities.id",)),
        sa.CheckConstraint(
            "status IN ('active', 'revoked', 'expired')",
            name="ck_auth_sessions_status",
        ),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_status", "auth_sessions", ["status"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

    with op.batch_alter_table("tenant_memberships") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tenant_memberships_user_id", "user_identities", ["user_id"], ["id"])
        batch.create_unique_constraint("uq_tenant_membership_user", ["tenant_id", "user_id"])
        batch.create_check_constraint(
            "ck_tenant_memberships_status", "status IN ('active', 'disabled')"
        )
        batch.create_index("ix_tenant_memberships_user_id", ["user_id"])

    op.create_table(
        "identity_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("event_code", sa.String(100), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.String(36), nullable=True),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("reason_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(("actor_user_id",), ("user_identities.id",)),
        sa.ForeignKeyConstraint(("target_user_id",), ("user_identities.id",)),
        sa.ForeignKeyConstraint(("tenant_id",), ("stores.id",)),
        sa.ForeignKeyConstraint(("session_id",), ("auth_sessions.id",)),
    )
    for column in ("event_code", "actor_user_id", "target_user_id", "tenant_id", "session_id", "created_at"):
        op.create_index(f"ix_identity_audit_logs_{column}", "identity_audit_logs", [column])


def downgrade() -> None:
    op.drop_table("identity_audit_logs")
    with op.batch_alter_table("tenant_memberships") as batch:
        batch.drop_index("ix_tenant_memberships_user_id")
        batch.drop_constraint("uq_tenant_membership_user", type_="unique")
        batch.drop_constraint("ck_tenant_memberships_status", type_="check")
        batch.drop_constraint("fk_tenant_memberships_user_id", type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_table("auth_sessions")
    op.drop_table("user_identities")
