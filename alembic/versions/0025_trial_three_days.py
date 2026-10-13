"""Set trial catalog durations to three days for future activations only.

Existing subscription expiry timestamps, order snapshots and history are not changed.
"""
from alembic import op
import sqlalchemy as sa

revision = "0025_trial_three_days"
down_revision = "0024_ai_assistant_v1_catalog"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.get_bind().execute(sa.text("""
        UPDATE saas_plans SET duration_days = 3
        WHERE code IN ('TRIAL', 'AUTOMATION_TRIAL', 'AI_ASSISTANT_TRIAL')
          AND duration_days IS DISTINCT FROM 3
    """))

def downgrade() -> None:
    # Historical duration policies must not be restored automatically.
    pass
