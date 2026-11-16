from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from app.models.product import ProductStatus


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    sku: str = Field(min_length=2, max_length=100)
    description: str | None = None
    category_id: int
    brand_id: int
    base_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    status: ProductStatus = ProductStatus.DRAFT
    is_featured: bool = False

    @field_validator("name", "sku")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value.strip()

    @field_validator("compare_at_price")
    @classmethod
    def validate_compare_price(cls, value, info):
        base_price = info.data.get("base_price")
        if value is not None and base_price is not None and value < base_price:
            raise ValueError("Compare price must be greater than or equal to base price")
        return value


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    status: ProductStatus | None = None
    is_featured: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    description: str | None
    category_id: int
    brand_id: int
    base_price: Decimal
    compare_at_price: Decimal | None
    status: ProductStatus
    is_featured: bool

    model_config = {"from_attributes": True}