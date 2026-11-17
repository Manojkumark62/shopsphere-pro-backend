
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.product import Product
    from app.models.product_variant import ProductVariant

class WarehouseInventory(Base):
    __tablename__ = "warehouse_inventories"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", "variant_id", name="uq_warehouse_product_variant"),
        CheckConstraint("quantity >= 0", name="ck_warehouse_quantity_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    warehouse: Mapped["Warehouse"] = relationship(back_populates="inventory_items")
    product: Mapped["Product"] = relationship(back_populates="warehouse_inventories")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="warehouse_inventories")
