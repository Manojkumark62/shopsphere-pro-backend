"""Create the missing warehouse inventory table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "d71f8a2c9b40"
down_revision: Union[str, Sequence[str], None] = "e5494dd3cf76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("warehouse_inventories"):
        return

    op.create_table(
        "warehouse_inventories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="ck_warehouse_quantity_nonnegative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "warehouse_id",
            "product_id",
            "variant_id",
            name="uq_warehouse_product_variant",
        ),
    )
    op.create_index("ix_warehouse_inventories_id", "warehouse_inventories", ["id"])
    op.create_index(
        "ix_warehouse_inventories_warehouse_id",
        "warehouse_inventories",
        ["warehouse_id"],
    )
    op.create_index(
        "ix_warehouse_inventories_product_id",
        "warehouse_inventories",
        ["product_id"],
    )
    op.create_index(
        "ix_warehouse_inventories_variant_id",
        "warehouse_inventories",
        ["variant_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if not inspect(bind).has_table("warehouse_inventories"):
        return

    op.drop_index("ix_warehouse_inventories_variant_id", table_name="warehouse_inventories")
    op.drop_index("ix_warehouse_inventories_product_id", table_name="warehouse_inventories")
    op.drop_index("ix_warehouse_inventories_warehouse_id", table_name="warehouse_inventories")
    op.drop_index("ix_warehouse_inventories_id", table_name="warehouse_inventories")
    op.drop_table("warehouse_inventories")
