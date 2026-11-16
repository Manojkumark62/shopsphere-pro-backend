"""Legacy revision retained for databases that recorded this revision.

The current application schema is reconciled by the forward repair revision.
"""
from typing import Sequence, Union


revision: str = "71eacdca5bc6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
