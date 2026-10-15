"""Add independently configurable Nagios data polling interval.

Revision ID: f6d2c8a1b390
Revises: e79b7d3c2641
"""
from alembic import op
import sqlalchemy as sa

revision = "f6d2c8a1b390"
down_revision = "e79b7d3c2641"
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table("SYSTEM_SETTINGS") as batch:
        batch.add_column(sa.Column("Data_Polling_Interval", sa.Integer(), nullable=False, server_default="60"))


def downgrade_():
    with op.batch_alter_table("SYSTEM_SETTINGS") as batch:
        batch.drop_column("Data_Polling_Interval")


def upgrade_history():
    pass


def downgrade_history():
    pass
