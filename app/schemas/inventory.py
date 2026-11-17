
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class InventoryAdjustment(BaseModel):
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=3, max_length=500)

class InventoryReservation(BaseModel):
    quantity: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=500)

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    variant_id: int | None
    quantity_on_hand: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

class InventoryMovementResponse(BaseModel):
    id: int
    inventory_id: int
    movement_type: str
    quantity: int
    quantity_before: int
    quantity_after: int
    reserved_before: int
    reserved_after: int
    reason: str | None
    performed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
