from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WishlistItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)


class WishlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    product_id: int
    variant_id: int | None
    created_at: datetime


class WishlistAvailabilityResponse(BaseModel):
    wishlist_item_id: int
    product_id: int
    variant_id: int | None
    available_quantity: int
    is_available: bool