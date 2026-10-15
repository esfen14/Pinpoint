"""Join NCPA/interface and interface/recipient migration histories.

Revision ID: f129a79e6301
Revises: e4a129c7b630, e79b7d3c2641

Preserve both previously published joins and their applied ancestors. The
normal multi-bind upgrade applies any missing branch before reaching this
schema-free join; no existing port, interface or recipient data is changed.
"""

revision = 'f129a79e6301'
down_revision = ('e4a129c7b630', 'e79b7d3c2641')
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()[f'upgrade_{engine_name}']()


def downgrade(engine_name):
    globals()[f'downgrade_{engine_name}']()


def upgrade_():
    pass


def downgrade_():
    pass


def upgrade_history():
    pass


def downgrade_history():
    pass
