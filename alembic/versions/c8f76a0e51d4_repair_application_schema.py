"""Create missing application tables while preserving existing data."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

from app.database.connection import Base
from app.models import (
    auth,
    brand,
    customer_address,
    customer_profile_management,
    customer_registration,
    product,
    product_category,
    product_media,
    product_variant,
    user_management,
)


revision: str = "c8f76a0e51d4"
down_revision: Union[str, Sequence[str], None] = "22b29eb8667e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)

    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "is_verified" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "is_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    # This repair may include pre-existing tables, so dropping them could destroy data.
    pass
