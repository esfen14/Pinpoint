"""Join interface monitoring and per-host recipient migration histories.

Revision ID: e79b7d3c2641
Revises: b7d3f1a9c264, a79e14c0b621

Both branches were already exercised independently. Joining them without
rewriting either parent supports upgrades from released interface installs
and the earlier recipient preview. The merge itself changes no schema/data.
"""

revision = 'e79b7d3c2641'
down_revision = ('b7d3f1a9c264', 'a79e14c0b621')
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
