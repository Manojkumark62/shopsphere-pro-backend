"""Legacy revision retained for databases that recorded this revision."""
from typing import Sequence, Union


revision: str = "22b29eb8667e"
down_revision: Union[str, Sequence[str], None] = "5b60f4138484"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
