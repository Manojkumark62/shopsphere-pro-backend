from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.inventory_transfer import (
    TransferMovementType,
    TransferStatus,
)


class InventoryTransferCreate(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    variant_id: int | None = None
    requested_quantity: int = Field(gt=0)
    note: str | None = None

    @model_validator(mode="after")
    def validate_warehouses(self):
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("Source and destination warehouses must differ")
        return self


class InventoryTransferDispatch(BaseModel):
    quantity: int = Field(gt=0)
    note: str | None = None


class InventoryTransferReceive(BaseModel):
    quantity: int = Field(gt=0)
    note: str | None = None


class InventoryTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    variant_id: int | None
    requested_quantity: int
    dispatched_quantity: int
    received_quantity: int
    status: TransferStatus
    note: str | None
    requested_by: int
    dispatched_by: int | None
    received_by: int | None
    created_at: datetime
    dispatched_at: datetime | None
    received_at: datetime | None


class TransferMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transfer_id: int
    movement_type: TransferMovementType
    quantity: int
    from_warehouse_id: int | None
    to_warehouse_id: int | None
    performed_by: int
    note: str | None
    created_at: datetime