"""Add normalized phone number storage for newly registered users."""

from alembic import op
import sqlalchemy as sa


revision = "0023_user_phone_number"
down_revision = "0022_durable_receipt_blob"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user_identities") as batch:
        batch.add_column(
            sa.Column(
                "phone_number",
                sa.String(length=13),
                nullable=True,
            )
        )


def downgrade():
    bind = op.get_bind()

    phone_count = bind.scalar(
        sa.text(
            """
            SELECT count(*)
            FROM user_identities
            WHERE phone_number IS NOT NULL
            """
        )
    )

    if phone_count:
        raise RuntimeError(
            "Cannot downgrade while registered phone numbers exist"
        )

    with op.batch_alter_table("user_identities") as batch:
        batch.drop_column("phone_number")
