from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductVariantCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=100)
    variant_name: str = Field(min_length=1, max_length=150)
    attributes: dict[str, object] = Field(default_factory=dict)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    compare_at_price: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )

    @field_validator("sku", "variant_name")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("compare_at_price")
    @classmethod
    def validate_compare_price(cls, value: Decimal | None, info) -> Decimal | None:
        price = info.data.get("price")
        if value is not None and price is not None and value < price:
            raise ValueError("Compare price must be greater than or equal to price")
        return value


class ProductVariantUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    variant_name: str | None = Field(default=None, min_length=1, max_length=150)
    attributes: dict[str, object] | None = None
    price: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    compare_at_price: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    is_active: bool | None = None

    @field_validator("sku", "variant_name")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    sku: str
    variant_name: str
    attributes: dict[str, object]
    price: Decimal
    compare_at_price: Decimal | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
