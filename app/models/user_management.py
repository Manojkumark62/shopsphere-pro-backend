
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base

class UserActivity(Base):
    __tablename__ = "user_activities"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    actor: Mapped["User"] = relationship(
        back_populates="activities_as_actor",
        foreign_keys=[actor_id],
    )
    target_user: Mapped["User"] = relationship(
        back_populates="activities_as_target",
        foreign_keys=[target_user_id],
    )
