"""Add stable device-to-user email alert selections.

Revision ID: a79e14c0b621
Revises: c5e2a8f4d716
"""
from alembic import op
import sqlalchemy as sa

revision = 'a79e14c0b621'
down_revision = 'c5e2a8f4d716'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()[f"upgrade_{engine_name}"]()


def downgrade(engine_name):
    globals()[f"downgrade_{engine_name}"]()


def upgrade_():
    # No assignments: existing hosts keep the system-wide contact group.
    op.create_table('HOST_ALERT_RECIPIENT',
                    sa.Column('NetDiscoveryID', sa.Integer(), nullable=False),
                    sa.Column('UserID', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['NetDiscoveryID'], ['NETWORK_DISCOVERY.NetDiscoveryID']),
                    sa.ForeignKeyConstraint(['UserID'], ['USER.UserID']),
                    sa.PrimaryKeyConstraint('NetDiscoveryID', 'UserID'))
    op.create_index('ix_HOST_ALERT_RECIPIENT_UserID', 'HOST_ALERT_RECIPIENT', ['UserID'])


def downgrade_():
    op.drop_index('ix_HOST_ALERT_RECIPIENT_UserID', table_name='HOST_ALERT_RECIPIENT')
    op.drop_table('HOST_ALERT_RECIPIENT')


def upgrade_history():
    pass


def downgrade_history():
    pass
