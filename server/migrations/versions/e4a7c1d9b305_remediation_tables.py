"""add the remediation action and run tables

Revision ID: e4a7c1d9b305
Revises: c5e2a8f4d716
"""
from alembic import op
import sqlalchemy as sa

revision = 'e4a7c1d9b305'
down_revision = 'c5e2a8f4d716'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table(
        'REMEDIATION_ACTION',
        sa.Column('Id', sa.Integer(), nullable=False),
        sa.Column('Name', sa.String(length=60), nullable=False),
        sa.Column('Action_Type', sa.Enum('RECORD_ONLY', name='remediationactiontype'), nullable=False),
        sa.Column('Scope_Kind', sa.Enum('SERVICE', 'HOST', name='remediationscope'), nullable=False),
        sa.Column('Host_Pattern', sa.String(length=100), nullable=False),
        sa.Column('Service_Pattern', sa.String(length=150), nullable=True),
        sa.Column('Parameters', sa.JSON(), nullable=False),
        sa.Column('Enabled', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('Max_Runs_Per_Hour', sa.Integer(), server_default='2', nullable=False),
        sa.Column('Cooldown_Seconds', sa.Integer(), server_default='600', nullable=False),
        sa.Column('Version', sa.Integer(), nullable=False),
        sa.Column('Updated_By', sa.Integer(), nullable=True),
        sa.Column('Updated_At', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['Updated_By'], ['USER.UserID']),
        sa.PrimaryKeyConstraint('Id'),
    )
    with op.batch_alter_table('REMEDIATION_ACTION') as batch_op:
        batch_op.create_index('ix_REMEDIATION_ACTION_Name', ['Name'], unique=True)
        batch_op.create_index('ix_REMEDIATION_ACTION_Updated_By', ['Updated_By'], unique=False)

    op.create_table(
        'REMEDIATION_RUN',
        sa.Column('Id', sa.Integer(), nullable=False),
        sa.Column('Event_Key', sa.String(length=64), nullable=False),
        sa.Column('Action_Id', sa.Integer(), nullable=True),
        sa.Column('Action_Name', sa.String(length=60), nullable=False),
        sa.Column('Hostname', sa.String(length=100), nullable=False),
        sa.Column('Service', sa.String(length=150), nullable=True),
        sa.Column('State', sa.Enum('OK', 'WARNING', 'CRITICAL', 'UNKNOWN', 'UP', 'DOWN', 'UNREACHABLE',
                                   name='remediationeventstate'), nullable=False),
        sa.Column('State_Type', sa.Enum('SOFT', 'HARD', name='remediationeventstatetype'), nullable=False),
        sa.Column('Attempt', sa.Integer(), nullable=False),
        sa.Column('Received_At', sa.DateTime(), nullable=False),
        sa.Column('Started_At', sa.DateTime(), nullable=True),
        sa.Column('Finished_At', sa.DateTime(), nullable=True),
        sa.Column('Outcome', sa.Enum('RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT', 'SKIPPED_COOLDOWN',
                                     'SKIPPED_HOURLY_CAP', 'SKIPPED_DISABLED', 'DISCARDED_MALFORMED',
                                     'INTERRUPTED', 'DUPLICATE', name='remediationoutcome'), nullable=False),
        sa.Column('Reason', sa.String(length=200), nullable=True),
        sa.Column('Output', sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint('Id'),
        sa.UniqueConstraint('Event_Key', 'Action_Id', name='uq_remediation_run_event_action'),
    )
    with op.batch_alter_table('REMEDIATION_RUN') as batch_op:
        batch_op.create_index('ix_REMEDIATION_RUN_Event_Key', ['Event_Key'], unique=False)
        batch_op.create_index('ix_REMEDIATION_RUN_Action_Id', ['Action_Id'], unique=False)
        batch_op.create_index('ix_REMEDIATION_RUN_Hostname', ['Hostname'], unique=False)
        batch_op.create_index('ix_REMEDIATION_RUN_Received_At', ['Received_At'], unique=False)
        batch_op.create_index('ix_REMEDIATION_RUN_Outcome', ['Outcome'], unique=False)


def downgrade_():
    with op.batch_alter_table('REMEDIATION_RUN') as batch_op:
        batch_op.drop_index('ix_REMEDIATION_RUN_Outcome')
        batch_op.drop_index('ix_REMEDIATION_RUN_Received_At')
        batch_op.drop_index('ix_REMEDIATION_RUN_Hostname')
        batch_op.drop_index('ix_REMEDIATION_RUN_Action_Id')
        batch_op.drop_index('ix_REMEDIATION_RUN_Event_Key')
    op.drop_table('REMEDIATION_RUN')
    with op.batch_alter_table('REMEDIATION_ACTION') as batch_op:
        batch_op.drop_index('ix_REMEDIATION_ACTION_Updated_By')
        batch_op.drop_index('ix_REMEDIATION_ACTION_Name')
    op.drop_table('REMEDIATION_ACTION')


def upgrade_history():
    pass


def downgrade_history():
    pass
