"""Add private Payexa verification token and reconciliation state."""
from alembic import op
import sqlalchemy as sa

revision = '0020_payexa_verification_token'
down_revision = '0019_kpay_payment_gateway'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('manual_payments') as batch:
        batch.add_column(sa.Column('provider_verification_token', sa.String(128), nullable=True))
        batch.drop_constraint('ck_manual_payments_provider_operation_state', type_='check')
        batch.create_check_constraint('ck_manual_payments_provider_operation_state', "provider_operation_state IS NULL OR provider_operation_state IN ('NOT_STARTED', 'CREATE_IN_FLIGHT', 'CREATED', 'CREATE_UNKNOWN', 'VERIFY_PENDING', 'PAID', 'FAILED', 'RECONCILIATION_REQUIRED')")


def downgrade():
    # Refuse a downgrade that could discard a real provider identity.
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM manual_payments WHERE provider = 'payexa' OR provider_verification_token IS NOT NULL OR provider_operation_state = 'RECONCILIATION_REQUIRED'")):
        raise RuntimeError('Cannot downgrade with Payexa payment evidence')
    with op.batch_alter_table('manual_payments') as batch:
        batch.drop_constraint('ck_manual_payments_provider_operation_state', type_='check')
        batch.create_check_constraint('ck_manual_payments_provider_operation_state', "provider_operation_state IS NULL OR provider_operation_state IN ('NOT_STARTED', 'CREATE_IN_FLIGHT', 'CREATED', 'CREATE_UNKNOWN', 'VERIFY_PENDING', 'PAID', 'FAILED')")
        batch.drop_column('provider_verification_token')
