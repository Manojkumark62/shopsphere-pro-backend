
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customer_profile: Mapped["CustomerProfile | None"] = relationship(back_populates="user", uselist=False)
    email_verifications: Mapped[list["EmailVerification"]] = relationship(back_populates="user")
    customer_addresses: Mapped[list["CustomerAddress"]] = relationship(back_populates="user")
    deactivation_requests: Mapped[list["AccountDeactivationRequest"]] = relationship(
        back_populates="user",
        foreign_keys="AccountDeactivationRequest.user_id",
    )
    deactivation_requests_reviewed: Mapped[list["AccountDeactivationRequest"]] = relationship(
        back_populates="reviewed_by_user",
        foreign_keys="AccountDeactivationRequest.reviewed_by",
    )
    profile_changes: Mapped[list["ProfileChangeHistory"]] = relationship(
        back_populates="user",
        foreign_keys="ProfileChangeHistory.user_id",
    )
    profile_changes_made: Mapped[list["ProfileChangeHistory"]] = relationship(
        back_populates="changed_by_user",
        foreign_keys="ProfileChangeHistory.changed_by_user_id",
    )
    activities_as_actor: Mapped[list["UserActivity"]] = relationship(
        back_populates="actor",
        foreign_keys="UserActivity.actor_id",
    )
    activities_as_target: Mapped[list["UserActivity"]] = relationship(
        back_populates="target_user",
        foreign_keys="UserActivity.target_user_id",
    )
    created_coupons: Mapped[list["Coupon"]] = relationship(back_populates="created_by_user")
    coupon_usages: Mapped[list["CouponUsage"]] = relationship(back_populates="customer")
    created_product_prices: Mapped[list["ProductPrice"]] = relationship(back_populates="created_by_user")
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="performed_by_user")
    requested_inventory_transfers: Mapped[list["InventoryTransfer"]] = relationship(
        back_populates="requested_by_user",
        foreign_keys="InventoryTransfer.requested_by",
    )
    dispatched_inventory_transfers: Mapped[list["InventoryTransfer"]] = relationship(
        back_populates="dispatched_by_user",
        foreign_keys="InventoryTransfer.dispatched_by",
    )
    received_inventory_transfers: Mapped[list["InventoryTransfer"]] = relationship(
        back_populates="received_by_user",
        foreign_keys="InventoryTransfer.received_by",
    )
    inventory_transfer_movements: Mapped[list["InventoryTransferMovement"]] = relationship(
        back_populates="performed_by_user"
    )
    changed_stock_thresholds: Mapped[list["StockThresholdHistory"]] = relationship(
        back_populates="changed_by_user"
    )
    wishlist_items: Mapped[list["WishlistItem"]] = relationship(back_populates="customer")
    shopping_carts: Mapped[list["ShoppingCart"]] = relationship(back_populates="customer")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class RevokedAccessToken(Base):
    __tablename__ = "revoked_access_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
