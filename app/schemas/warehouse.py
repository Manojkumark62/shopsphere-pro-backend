
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=50)
    address: str = Field(min_length=5, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=2, max_length=20)
    capacity_units: int = Field(gt=0)

class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=2, max_length=20)
    capacity_units: int | None = Field(default=None, gt=0)
    status: Literal["active", "inactive", "maintenance"] | None = None

class WarehouseResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    capacity_units: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WarehouseStockCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    quantity: int = Field(ge=0)

class WarehouseStockResponse(BaseModel):
    id: int
    warehouse_id: int
    product_id: int
    variant_id: int | None
    quantity: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
