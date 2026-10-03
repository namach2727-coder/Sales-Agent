"""Add admin-managed payment cards and immutable payment card snapshots."""

from alembic import op
import sqlalchemy as sa


revision = "0021_admin_payment_cards"
down_revision = "0020_payexa_verification_token"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("card_number", sa.String(length=32), nullable=False),
        sa.Column("account_number", sa.String(length=64), nullable=True),
        sa.Column("account_name", sa.String(length=200), nullable=False),
        sa.Column("bank_name", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "revision >= 1",
            name="ck_payment_cards_revision",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "card_number",
            name="uq_payment_cards_card_number",
        ),
    )

    op.create_index(
        "ix_payment_cards_public_id",
        "payment_cards",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_payment_cards_is_active",
        "payment_cards",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_payment_cards_is_default",
        "payment_cards",
        ["is_default"],
        unique=False,
    )

    with op.batch_alter_table("manual_payments") as batch:
        batch.add_column(
            sa.Column("payment_card_id", sa.Integer(), nullable=True)
        )
        batch.add_column(
            sa.Column("card_number_snapshot", sa.String(length=32), nullable=True)
        )
        batch.add_column(
            sa.Column("account_number_snapshot", sa.String(length=64), nullable=True)
        )
        batch.add_column(
            sa.Column("account_name_snapshot", sa.String(length=200), nullable=True)
        )
        batch.add_column(
            sa.Column("bank_name_snapshot", sa.String(length=120), nullable=True)
        )

        batch.create_foreign_key(
            "fk_manual_payments_payment_card_id_payment_cards",
            "payment_cards",
            ["payment_card_id"],
            ["id"],
        )
        batch.create_index(
            "ix_manual_payments_payment_card_id",
            ["payment_card_id"],
            unique=False,
        )


def downgrade():
    bind = op.get_bind()

    card_count = bind.scalar(
        sa.text("SELECT count(*) FROM payment_cards")
    )
    snapshot_count = bind.scalar(
        sa.text(
            """
            SELECT count(*)
            FROM manual_payments
            WHERE payment_card_id IS NOT NULL
               OR card_number_snapshot IS NOT NULL
               OR account_number_snapshot IS NOT NULL
               OR account_name_snapshot IS NOT NULL
               OR bank_name_snapshot IS NOT NULL
            """
        )
    )

    if card_count or snapshot_count:
        raise RuntimeError(
            "Cannot downgrade while payment-card evidence exists"
        )

    with op.batch_alter_table("manual_payments") as batch:
        batch.drop_index("ix_manual_payments_payment_card_id")
        batch.drop_constraint(
            "fk_manual_payments_payment_card_id_payment_cards",
            type_="foreignkey",
        )
        batch.drop_column("bank_name_snapshot")
        batch.drop_column("account_name_snapshot")
        batch.drop_column("account_number_snapshot")
        batch.drop_column("card_number_snapshot")
        batch.drop_column("payment_card_id")

    op.drop_index(
        "ix_payment_cards_is_default",
        table_name="payment_cards",
    )
    op.drop_index(
        "ix_payment_cards_is_active",
        table_name="payment_cards",
    )
    op.drop_index(
        "ix_payment_cards_public_id",
        table_name="payment_cards",
    )
    op.drop_table("payment_cards")
