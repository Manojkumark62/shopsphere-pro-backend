from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_id: int
    product_id: int
    variant_id: int | None
    quantity: int
    created_at: datetime
    updated_at: datetime


class ShoppingCartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse] = Field(default_factory=list)


class CartAvailabilityResponse(BaseModel):
    product_id: int
    variant_id: int | None
    requested_quantity: int
    available_quantity: int
    is_available: bool