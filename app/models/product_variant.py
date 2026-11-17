from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_media import ProductMedia
    from app.models.product_pricing import ProductPrice
    from app.models.inventory import Inventory
    from app.models.cart import CartItem
    from app.models.wishlist import WishlistItem
    from app.models.inventory_transfer import InventoryTransfer
    from app.models.warehouse_inventory import WarehouseInventory
    from app.models.low_stock import StockThreshold
    from app.models.low_stock import StockRestockAlert


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    variant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    compare_at_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    product: Mapped["Product"] = relationship(back_populates="variants")
    media: Mapped[list["ProductMedia"]] = relationship(back_populates="variant")
    prices: Mapped[list["ProductPrice"]] = relationship(back_populates="variant")
    inventories: Mapped[list["Inventory"]] = relationship(back_populates="variant")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="variant")
    wishlist_items: Mapped[list["WishlistItem"]] = relationship(back_populates="variant")
    inventory_transfers: Mapped[list["InventoryTransfer"]] = relationship(back_populates="variant")
    warehouse_inventories: Mapped[list["WarehouseInventory"]] = relationship(back_populates="variant")
    stock_thresholds: Mapped[list["StockThreshold"]] = relationship(back_populates="variant")
    restock_alerts: Mapped[list["StockRestockAlert"]] = relationship(back_populates="variant")