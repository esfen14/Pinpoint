"""add system-wide Nagios flap detection settings

Revision ID: c5e2a8f4d716
Revises: b7d3f1a9c8e5
"""
from alembic import op
import sqlalchemy as sa

revision = 'c5e2a8f4d716'
down_revision = 'b7d3f1a9c8e5'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    # Detection stays on and no threshold is set, which is what the generated
    # config does today (Nagios's global values apply).
    with op.batch_alter_table('SYSTEM_SETTINGS') as batch_op:
        batch_op.add_column(sa.Column('Flap_Detection_Enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column('Flap_Low_Threshold', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('Flap_High_Threshold', sa.Float(), nullable=True))


def downgrade_():
    with op.batch_alter_table('SYSTEM_SETTINGS') as batch_op:
        batch_op.drop_column('Flap_High_Threshold')
        batch_op.drop_column('Flap_Low_Threshold')
        batch_op.drop_column('Flap_Detection_Enabled')


def upgrade_history():
    pass


def downgrade_history():
    pass
