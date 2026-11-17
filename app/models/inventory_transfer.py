
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class TransferMovementType(str, enum.Enum):
    REQUESTED = "requested"
    DISPATCHED = "dispatched"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    source_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )
    destination_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id"), nullable=False, index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id"), nullable=True, index=True
    )

    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    dispatched_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[TransferStatus] = mapped_column(
        SAEnum(TransferStatus, native_enum=False),
        default=TransferStatus.PENDING,
        nullable=False,
        index=True,
    )

    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    dispatched_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    received_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_warehouse: Mapped["Warehouse"] = relationship(
        back_populates="source_transfers",
        foreign_keys=[source_warehouse_id],
    )
    destination_warehouse: Mapped["Warehouse"] = relationship(
        back_populates="destination_transfers",
        foreign_keys=[destination_warehouse_id],
    )
    product: Mapped["Product"] = relationship(back_populates="inventory_transfers")
    variant: Mapped["ProductVariant | None"] = relationship(back_populates="inventory_transfers")
    requested_by_user: Mapped["User"] = relationship(
        back_populates="requested_inventory_transfers",
        foreign_keys=[requested_by],
    )
    dispatched_by_user: Mapped["User | None"] = relationship(
        back_populates="dispatched_inventory_transfers",
        foreign_keys=[dispatched_by],
    )
    received_by_user: Mapped["User | None"] = relationship(
        back_populates="received_inventory_transfers",
        foreign_keys=[received_by],
    )
    movements: Mapped[list["InventoryTransferMovement"]] = relationship(back_populates="transfer")


class InventoryTransferMovement(Base):
    __tablename__ = "inventory_transfer_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("inventory_transfers.id"), nullable=False, index=True
    )

    movement_type: Mapped[TransferMovementType] = mapped_column(
        SAEnum(TransferMovementType, native_enum=False),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    from_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id"), nullable=True
    )
    to_warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id"), nullable=True
    )

    performed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    transfer: Mapped["InventoryTransfer"] = relationship(back_populates="movements")
    from_warehouse: Mapped["Warehouse | None"] = relationship(
        back_populates="transfers_from",
        foreign_keys=[from_warehouse_id],
    )
    to_warehouse: Mapped["Warehouse | None"] = relationship(
        back_populates="transfers_to",
        foreign_keys=[to_warehouse_id],
    )
    performed_by_user: Mapped["User"] = relationship(back_populates="inventory_transfer_movements")