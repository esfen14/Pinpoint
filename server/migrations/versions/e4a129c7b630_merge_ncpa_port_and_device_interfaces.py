"""Merge deployed NCPA ports and device interfaces without rewriting prior revisions.

Revision ID: e4a129c7b630
Revises: 7db78f308ee5, b7d3f1a9c264

Both branches descend from c5e2a8f4d716 and may already be installed. Joining
those heads lets the normal multi-bind upgrade apply whichever branch is missing.
The join itself changes neither schema nor data on either database bind.
"""

revision = 'e4a129c7b630'
down_revision = ('7db78f308ee5', 'b7d3f1a9c264')
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
