"""add maintenance windows and their occurrences

MAINTENANCE_WINDOW holds planned maintenance that PinPoint turns into Nagios scheduled
downtime; MAINTENANCE_OCCURRENCE records each occurrence handed to Nagios (unique per window
and start, so none is scheduled twice). With no rows nothing changes. The downgrade drops both
tables. history.db is not touched. Run `flask sync-permissions` afterwards to add the
maintenance.manage permission (granted to Administrator).

Revision ID: a4c8e1b7d933
Revises: b7d3f1a9c264
Create Date: 2026-10-15 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4c8e1b7d933'
down_revision = 'b7d3f1a9c264'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table('MAINTENANCE_WINDOW',
    sa.Column('WindowID', sa.Integer(), nullable=False),
    sa.Column('Start_At', sa.DateTime(), nullable=False),
    sa.Column('End_At', sa.DateTime(), nullable=False),
    sa.Column('Recurrence', sa.String(length=10), nullable=False),
    sa.Column('Recurrence_Until', sa.DateTime(), nullable=True),
    sa.Column('Time_Zone', sa.String(length=64), nullable=False),
    sa.Column('Comment', sa.String(length=255), nullable=False),
    sa.Column('Status', sa.String(length=20), nullable=False),
    sa.Column('Last_Occurrence_Sent', sa.DateTime(), nullable=True),
    sa.Column('Created_At', sa.DateTime(), nullable=False),
    sa.Column('NetDiscoveryID', sa.Integer(), nullable=True),
    sa.Column('Created_By', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['Created_By'], ['USER.UserID'], ),
    sa.ForeignKeyConstraint(['NetDiscoveryID'], ['NETWORK_DISCOVERY.NetDiscoveryID'], ),
    sa.PrimaryKeyConstraint('WindowID')
    )
    with op.batch_alter_table('MAINTENANCE_WINDOW', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_MAINTENANCE_WINDOW_Created_By'), ['Created_By'], unique=False)
        batch_op.create_index(batch_op.f('ix_MAINTENANCE_WINDOW_NetDiscoveryID'), ['NetDiscoveryID'], unique=False)
        batch_op.create_index(batch_op.f('ix_MAINTENANCE_WINDOW_Status'), ['Status'], unique=False)

    op.create_table('MAINTENANCE_OCCURRENCE',
    sa.Column('OccurrenceID', sa.Integer(), nullable=False),
    sa.Column('Start_At', sa.DateTime(), nullable=False),
    sa.Column('End_At', sa.DateTime(), nullable=False),
    sa.Column('Status', sa.String(length=20), nullable=False),
    sa.Column('Attempts', sa.Integer(), nullable=False),
    sa.Column('Last_Error', sa.String(length=255), nullable=True),
    sa.Column('Sent_At', sa.DateTime(), nullable=True),
    sa.Column('WindowID', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['WindowID'], ['MAINTENANCE_WINDOW.WindowID'], ),
    sa.PrimaryKeyConstraint('OccurrenceID'),
    sa.UniqueConstraint('WindowID', 'Start_At', name='uq_maintenance_occurrence_start')
    )
    with op.batch_alter_table('MAINTENANCE_OCCURRENCE', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_MAINTENANCE_OCCURRENCE_WindowID'), ['WindowID'], unique=False)


def downgrade_():
    with op.batch_alter_table('MAINTENANCE_OCCURRENCE', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_MAINTENANCE_OCCURRENCE_WindowID'))

    op.drop_table('MAINTENANCE_OCCURRENCE')
    with op.batch_alter_table('MAINTENANCE_WINDOW', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_MAINTENANCE_WINDOW_Status'))
        batch_op.drop_index(batch_op.f('ix_MAINTENANCE_WINDOW_NetDiscoveryID'))
        batch_op.drop_index(batch_op.f('ix_MAINTENANCE_WINDOW_Created_By'))

    op.drop_table('MAINTENANCE_WINDOW')


def upgrade_history():
    pass


def downgrade_history():
    pass
