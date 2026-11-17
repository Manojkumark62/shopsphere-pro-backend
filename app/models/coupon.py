from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (CheckConstraint("discount_value > 0", name="ck_coupon_discount_value_positive"), CheckConstraint("min_purchase >= 0", name="ck_coupon_min_purchase_nonnegative"), CheckConstraint("max_discount IS NULL OR max_discount > 0", name="ck_coupon_max_discount_positive"), CheckConstraint("usage_limit IS NULL OR usage_limit > 0", name="ck_coupon_usage_limit_positive"), CheckConstraint("per_customer_limit IS NULL OR per_customer_limit > 0", name="ck_coupon_customer_limit_positive"), Index("ix_coupons_code_active", "code", "is_active"))
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    max_discount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_customer_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_user: Mapped["User"] = relationship(back_populates="created_coupons")
    usages: Mapped[list["CouponUsage"]] = relationship(back_populates="coupon")

class CouponUsage(Base):
    __tablename__ = "coupon_usages"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    order_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    used_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    coupon: Mapped["Coupon"] = relationship(back_populates="usages")
    customer: Mapped["User"] = relationship(back_populates="coupon_usages")