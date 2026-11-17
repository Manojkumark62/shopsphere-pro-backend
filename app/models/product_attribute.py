
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.product_category import ProductCategory


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    data_type: Mapped[str] = mapped_column(String(30), default="text", nullable=False)
    allowed_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    category_assignments: Mapped[list["CategoryAttribute"]] = relationship(back_populates="attribute")
    product_values: Mapped[list["ProductAttributeValue"]] = relationship(back_populates="attribute")

class CategoryAttribute(Base):
    __tablename__ = "category_attributes"
    __table_args__ = (UniqueConstraint("category_id", "attribute_id", name="uq_category_attribute"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_categories.id"), nullable=False, index=True)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("product_attributes.id"), nullable=False, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    category: Mapped["ProductCategory"] = relationship(back_populates="attribute_assignments")
    attribute: Mapped["ProductAttribute"] = relationship(back_populates="category_assignments")

class ProductAttributeValue(Base):
    __tablename__ = "product_attribute_values"
    __table_args__ = (UniqueConstraint("product_id", "attribute_id", name="uq_product_attribute_value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("product_attributes.id"), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    product: Mapped["Product"] = relationship(back_populates="attribute_values")
    attribute: Mapped["ProductAttribute"] = relationship(back_populates="product_values")
