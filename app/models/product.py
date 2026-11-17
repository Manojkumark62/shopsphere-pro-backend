from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database.connection import Base


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_categories.id"), nullable=False)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    compare_at_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.DRAFT, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    category: Mapped["ProductCategory"] = relationship(back_populates="products")
    brand: Mapped["Brand"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product")
    media: Mapped[list["ProductMedia"]] = relationship(back_populates="product")
    attribute_values: Mapped[list["ProductAttributeValue"]] = relationship(back_populates="product")
    prices: Mapped[list["ProductPrice"]] = relationship(back_populates="product")
    inventories: Mapped[list["Inventory"]] = relationship(back_populates="product")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="product")
    wishlist_items: Mapped[list["WishlistItem"]] = relationship(back_populates="product")
    inventory_transfers: Mapped[list["InventoryTransfer"]] = relationship(back_populates="product")
    warehouse_inventories: Mapped[list["WarehouseInventory"]] = relationship(back_populates="product")
    stock_thresholds: Mapped[list["StockThreshold"]] = relationship(back_populates="product")
    restock_alerts: Mapped[list["StockRestockAlert"]] = relationship(back_populates="product")