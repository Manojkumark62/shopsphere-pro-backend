from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StockThresholdCreate(BaseModel):
    warehouse_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    minimum_quantity: int = Field(ge=0)
    reason: str | None = None


class StockThresholdUpdate(BaseModel):
    minimum_quantity: int = Field(ge=0)
    reason: str | None = None


class StockThresholdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    warehouse_id: int
    product_id: int
    variant_id: int | None
    minimum_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LowStockItemResponse(BaseModel):
    warehouse_id: int
    product_id: int
    variant_id: int | None
    current_quantity: int
    minimum_quantity: int
    shortage_quantity: int


class StockThresholdHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    threshold_id: int
    old_quantity: int | None
    new_quantity: int
    changed_by: int
    reason: str | None
    created_at: datetime


class RestockAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    warehouse_id: int
    product_id: int
    variant_id: int | None
    threshold_id: int
    current_quantity: int
    minimum_quantity: int
    status: str
    created_at: datetime
    resolved_at: datetime | None