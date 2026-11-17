
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.user_management import User


class InventoryMovementType(str, enum.Enum):
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    RESERVE = "reserve"
    RELEASE = "release"
    FULFILL = "fulfill"

class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("product_id", "variant_id", name="uq_inventory_product_variant"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_on_hand_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint("reserved_quantity <= quantity_on_hand", name="ck_inventory_reserved_lte_on_hand"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True, index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    product: Mapped["Product"] = relationship(back_populates="inventories")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="inventories")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="inventory")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventories.id"), nullable=False, index=True)
    movement_type: Mapped[InventoryMovementType] = mapped_column(Enum(InventoryMovementType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_before: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    inventory: Mapped["Inventory"] = relationship(back_populates="movements")
    performed_by_user: Mapped["User"] = relationship(back_populates="inventory_movements")
