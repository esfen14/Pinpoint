"""remediation failure escalation: Notify_On, run notification state, repeat settings

Adds REMEDIATION_ACTION.Notify_On (JSON list, default failed, capped and repeated),
REMEDIATION_RUN.Notify_Kind, Notify_State, Notify_Attempts, Notify_Error and Notify_At (all empty
or zero for existing runs, which means no notification was due), and
SYSTEM_SETTINGS.Remediation_Repeat_Count (default 3) and Remediation_Repeat_Window_Hours (default
24). Existing rows keep today's behavior. The downgrade drops the added columns.

history.db is not touched.

Revision ID: e153c4a8b2d7
Revises: f155a3c7d2b1
"""
from alembic import op
import sqlalchemy as sa

revision = 'e153c4a8b2d7'
down_revision = 'f155a3c7d2b1'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table('SYSTEM_SETTINGS', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Remediation_Repeat_Count', sa.Integer(), nullable=False, server_default='3'))
        batch_op.add_column(
            sa.Column('Remediation_Repeat_Window_Hours', sa.Integer(), nullable=False, server_default='24'))
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'Notify_On', sa.JSON(), nullable=False, server_default='["failed", "capped", "repeated"]'))
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Notify_Kind', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column(
            'Notify_State', sa.Enum('PENDING', 'SENT', 'FAILED', name='remediationnotifystate'), nullable=True))
        batch_op.add_column(sa.Column('Notify_Attempts', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('Notify_Error', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('Notify_At', sa.DateTime(), nullable=True))


def downgrade_():
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.drop_column('Notify_At')
        batch_op.drop_column('Notify_Error')
        batch_op.drop_column('Notify_Attempts')
        batch_op.drop_column('Notify_State')
        batch_op.drop_column('Notify_Kind')
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.drop_column('Notify_On')
    with op.batch_alter_table('SYSTEM_SETTINGS', schema=None) as batch_op:
        batch_op.drop_column('Remediation_Repeat_Window_Hours')
        batch_op.drop_column('Remediation_Repeat_Count')


def upgrade_history():
    pass


def downgrade_history():
    pass
