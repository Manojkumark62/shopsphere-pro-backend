from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.warehouse import Warehouse
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.user_management import User
    
class StockThreshold(Base):
    __tablename__ = "stock_thresholds"
    __table_args__ = (UniqueConstraint("warehouse_id", "product_id", "variant_id", name="uq_stock_threshold"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True, index=True)
    minimum_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    warehouse: Mapped["Warehouse"] = relationship(back_populates="stock_thresholds")
    product: Mapped["Product"] = relationship(back_populates="stock_thresholds")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="stock_thresholds")
    history: Mapped[list["StockThresholdHistory"]] = relationship(back_populates="threshold")
    alerts: Mapped[list["StockRestockAlert"]] = relationship(back_populates="threshold")


class StockThresholdHistory(Base):
    __tablename__ = "stock_threshold_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    threshold_id: Mapped[int] = mapped_column(ForeignKey("stock_thresholds.id"), nullable=False, index=True)
    old_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    threshold: Mapped["StockThreshold"] = relationship(back_populates="history")
    changed_by_user: Mapped["User"] = relationship(back_populates="changed_stock_thresholds")


class StockRestockAlert(Base):
    __tablename__ = "stock_restock_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True, index=True)
    threshold_id: Mapped[int] = mapped_column(ForeignKey("stock_thresholds.id"), nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    warehouse: Mapped["Warehouse"] = relationship(back_populates="restock_alerts")
    product: Mapped["Product"] = relationship(back_populates="restock_alerts")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="restock_alerts")
    threshold: Mapped["StockThreshold"] = relationship(back_populates="alerts")