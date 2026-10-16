"""Join manual topology with maintenance and remediation restart histories

Revision ID: d117f3b8a053
Revises: c117e6a9d042, b8e3d5f2a417
Create Date: 2026-10-16 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd117f3b8a053'
down_revision = ('c117e6a9d042', 'b8e3d5f2a417')
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    pass


def downgrade_():
    pass


def upgrade_history():
    pass


def downgrade_history():
    pass

