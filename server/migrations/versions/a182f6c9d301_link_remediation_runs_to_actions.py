"""Link remediation runs to actions; retain audit snapshots on deletion.

Generated with Flask-Migrate against both binds. The pre-constraint cleanup
nulls orphan links from deleted actions; no audit rows are removed. Downgrade
removes only the constraint and cannot reconstruct formerly orphaned links.

Revision ID: a182f6c9d301
Revises: c7a1f4d92e60
Create Date: 2026-10-17 12:18:29.016606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a182f6c9d301'
down_revision = 'c7a1f4d92e60'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    op.execute(sa.text(
        'UPDATE REMEDIATION_RUN SET Action_Id = NULL '
        'WHERE Action_Id IS NOT NULL AND NOT EXISTS '
        '(SELECT 1 FROM REMEDIATION_ACTION WHERE Id = REMEDIATION_RUN.Action_Id)'
    ))
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_remediation_run_action', 'REMEDIATION_ACTION', ['Action_Id'], ['Id'], ondelete='SET NULL')



def downgrade_():
    with op.batch_alter_table('REMEDIATION_RUN', schema=None) as batch_op:
        batch_op.drop_constraint('fk_remediation_run_action', type_='foreignkey')



def upgrade_history():
    pass


def downgrade_history():
    pass

