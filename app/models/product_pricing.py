
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, Boolean, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_management import User
    from app.models.product import Product
    from app.models.product_variant import ProductVariant

class ProductPrice(Base):
    __tablename__ = "product_prices"
    __table_args__ = (Index("ix_product_price_lookup", "product_id", "variant_id", "is_active"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True, index=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    product: Mapped["Product"] = relationship(back_populates="prices")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="prices")
    created_by_user: Mapped["User"] = relationship(back_populates="created_product_prices")
