from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductPriceCreate(BaseModel):
    variant_id: int | None = Field(default=None, gt=0)
    base_price: Decimal = Field(gt=0)
    sale_price: Decimal | None = Field(default=None, gt=0)
    valid_from: datetime
    valid_until: datetime | None = None
    is_active: bool = True


class ProductPriceUpdate(BaseModel):
    variant_id: int | None = Field(default=None, gt=0)
    base_price: Decimal | None = Field(default=None, gt=0)
    sale_price: Decimal | None = Field(default=None, gt=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None


class ProductPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None
    base_price: Decimal
    sale_price: Decimal | None
    valid_from: datetime
    valid_until: datetime | None
    is_active: bool
    created_by: int
    created_at: datetime
