"""server-side sign-in records: USER_SESSION

Adds the USER_SESSION table, one row per sign-in, so logout can revoke a session
on the server. No existing data changes. Sessions signed in before the upgrade
have no row, so everyone signs in once. The downgrade drops the table.

history.db is not touched.

Revision ID: a339c5e2d481
Revises: e153c4a8b2d7
"""
from alembic import op
import sqlalchemy as sa

revision = 'a339c5e2d481'
down_revision = 'e153c4a8b2d7'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table(
        'USER_SESSION',
        sa.Column('SessionID', sa.String(length=64), nullable=False),
        sa.Column('UserID', sa.Integer(), nullable=False),
        sa.Column('Created_At', sa.DateTime(), nullable=False),
        sa.Column('Last_Activity', sa.DateTime(), nullable=False),
        sa.Column('Remembered', sa.Boolean(), nullable=False),
        sa.Column('Revoked_At', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['UserID'], ['USER.UserID'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('SessionID'),
    )
    with op.batch_alter_table('USER_SESSION', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_USER_SESSION_UserID'), ['UserID'], unique=False)


def downgrade_():
    op.drop_table('USER_SESSION')


def upgrade_history():
    pass


def downgrade_history():
    pass
