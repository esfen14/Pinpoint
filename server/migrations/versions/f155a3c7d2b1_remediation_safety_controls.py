"""remediation safety controls: kill switch, retention, run-when-acknowledged, consumer state

Adds SYSTEM_SETTINGS.Remediation_Enabled (default on) and Remediation_Retention_Days (default 90),
REMEDIATION_ACTION.Run_When_Acknowledged (default off), four skip outcomes on
REMEDIATION_RUN.Outcome, and the one-row REMEDIATION_CONSUMER_STATE table. Existing rows keep
today's behavior. The downgrade deletes runs with a new outcome (the older schema cannot hold
them) and drops the added columns and table.

history.db is not touched.

Revision ID: f155a3c7d2b1
Revises: b7e2a9c4d518
"""
from alembic import op
import sqlalchemy as sa

revision = 'f155a3c7d2b1'
down_revision = 'b7e2a9c4d518'
branch_labels = None
depends_on = None

OLD_OUTCOMES = (
    'RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT', 'SKIPPED_COOLDOWN', 'SKIPPED_HOURLY_CAP', 'INTERRUPTED')
NEW_OUTCOMES = OLD_OUTCOMES + (
    'SKIPPED_KILL_SWITCH', 'SKIPPED_MAINTENANCE', 'SKIPPED_DOWNTIME', 'SKIPPED_ACKNOWLEDGED')


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table('SYSTEM_SETTINGS', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Remediation_Enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('Remediation_Retention_Days', sa.Integer(), nullable=False, server_default='90'))
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Run_When_Acknowledged', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.alter_column(
            'Outcome',
            existing_type=sa.Enum(*OLD_OUTCOMES, name='remediationoutcome'),
            type_=sa.Enum(*NEW_OUTCOMES, name='remediationoutcome'),
            existing_nullable=False)
    op.create_table(
        'REMEDIATION_CONSUMER_STATE',
        sa.Column('Id', sa.Integer(), nullable=False),
        sa.Column('Last_Tick_At', sa.DateTime(), nullable=True),
        sa.Column('Last_Error', sa.String(length=200), nullable=True),
        sa.Column('Dropped_Count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('Dropped_At', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('Id'))


def downgrade_():
    op.drop_table('REMEDIATION_CONSUMER_STATE')
    names = ", ".join("'%s'" % name for name in NEW_OUTCOMES[len(OLD_OUTCOMES):])
    op.get_bind().execute(sa.text("DELETE FROM REMEDIATION_RUN WHERE Outcome IN (%s)" % names))
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.alter_column(
            'Outcome',
            existing_type=sa.Enum(*NEW_OUTCOMES, name='remediationoutcome'),
            type_=sa.Enum(*OLD_OUTCOMES, name='remediationoutcome'),
            existing_nullable=False)
    with op.batch_alter_table('REMEDIATION_ACTION', schema=None) as batch_op:
        batch_op.drop_column('Run_When_Acknowledged')
    with op.batch_alter_table('SYSTEM_SETTINGS', schema=None) as batch_op:
        batch_op.drop_column('Remediation_Retention_Days')
        batch_op.drop_column('Remediation_Enabled')


def upgrade_history():
    pass


def downgrade_history():
    pass
