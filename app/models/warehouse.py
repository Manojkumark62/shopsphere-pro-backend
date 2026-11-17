
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.warehouse_inventory import WarehouseInventory
    from app.models.inventory_transfer import InventoryTransfer
    from app.models.low_stock import StockThreshold
    from app.models.low_stock import StockRestockAlert
    from app.models.inventory_transfer import InventoryTransferMovement

class WarehouseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity_units: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WarehouseStatus] = mapped_column(Enum(WarehouseStatus), default=WarehouseStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    inventory_items: Mapped[list["WarehouseInventory"]] = relationship(back_populates="warehouse")
    source_transfers: Mapped[list["InventoryTransfer"]] = relationship(
        back_populates="source_warehouse",
        foreign_keys="InventoryTransfer.source_warehouse_id",
    )
    destination_transfers: Mapped[list["InventoryTransfer"]] = relationship(
        back_populates="destination_warehouse",
        foreign_keys="InventoryTransfer.destination_warehouse_id",
    )
    stock_thresholds: Mapped[list["StockThreshold"]] = relationship(back_populates="warehouse")
    restock_alerts: Mapped[list["StockRestockAlert"]] = relationship(back_populates="warehouse")
    transfers_from: Mapped[list["InventoryTransferMovement"]] = relationship(
        back_populates="from_warehouse",
        foreign_keys="InventoryTransferMovement.from_warehouse_id",
    )
    transfers_to: Mapped[list["InventoryTransferMovement"]] = relationship(
        back_populates="to_warehouse",
        foreign_keys="InventoryTransferMovement.to_warehouse_id",
    )
