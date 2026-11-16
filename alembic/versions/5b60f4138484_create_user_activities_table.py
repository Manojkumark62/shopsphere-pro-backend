"""Legacy revision retained for databases that recorded this revision."""
from typing import Sequence, Union


revision: str = "5b60f4138484"
down_revision: Union[str, Sequence[str], None] = "71eacdca5bc6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
