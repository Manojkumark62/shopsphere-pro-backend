from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.database.connection import Base


class DeactivationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ProfileChangeHistory(Base):
    __tablename__ = "profile_change_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    user: Mapped["User"] = relationship(
        back_populates="profile_changes",
        foreign_keys=[user_id],
    )
    changed_by_user: Mapped["User"] = relationship(
        back_populates="profile_changes_made",
        foreign_keys=[changed_by_user_id],
    )


class AccountDeactivationRequest(Base):
    __tablename__ = "account_deactivation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DeactivationStatus] = mapped_column(Enum(DeactivationStatus), default=DeactivationStatus.PENDING, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user: Mapped["User"] = relationship(
        back_populates="deactivation_requests",
        foreign_keys=[user_id],
    )
    reviewed_by_user: Mapped["User | None"] = relationship(
        back_populates="deactivation_requests_reviewed",
        foreign_keys=[reviewed_by],
    )