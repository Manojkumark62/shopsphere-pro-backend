from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_type: Literal["percentage", "fixed"]
    discount_value: Decimal = Field(gt=0)
    min_purchase: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_discount: Decimal | None = Field(default=None, gt=0)
    usage_limit: int | None = Field(default=None, gt=0)
    per_customer_limit: int | None = Field(default=None, gt=0)
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("valid_until")
    @classmethod
    def ensure_valid_window(cls, value: datetime, info):
        if info.data.get("valid_from") and value <= info.data["valid_from"]:
            raise ValueError("valid_until must be later than valid_from")
        return value


class CouponUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=50)
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: Decimal | None = Field(default=None, gt=0)
    min_purchase: Decimal | None = Field(default=None, ge=0)
    max_discount: Decimal | None = Field(default=None, gt=0)
    usage_limit: int | None = Field(default=None, gt=0)
    per_customer_limit: int | None = Field(default=None, gt=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper()


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    discount_type: str
    discount_value: Decimal
    min_purchase: Decimal
    max_discount: Decimal | None
    usage_limit: int | None
    per_customer_limit: int | None
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime