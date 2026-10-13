"""add system-wide Nagios retry interval and maximum check attempts

Revision ID: b7d3f1a9c8e5
Revises: a4c8e1f6d392
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7d3f1a9c8e5'
down_revision = 'a4c8e1f6d392'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    # The defaults are the values the generated config always used, so an
    # existing install keeps producing the same Nagios config.
    with op.batch_alter_table('SYSTEM_SETTINGS') as batch_op:
        batch_op.add_column(sa.Column('Retry_Interval', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('Max_Check_Attempts', sa.Integer(), nullable=False, server_default='3'))


def downgrade_():
    with op.batch_alter_table('SYSTEM_SETTINGS') as batch_op:
        batch_op.drop_column('Max_Check_Attempts')
        batch_op.drop_column('Retry_Interval')


def upgrade_history():
    pass


def downgrade_history():
    pass
