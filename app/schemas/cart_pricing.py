from decimal import Decimal
from pydantic import BaseModel, Field


class CartPricingRequest(BaseModel):
    coupon_code: str | None = None
    shipping_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class CartItemPriceResponse(BaseModel):
    cart_item_id: int
    product_id: int
    variant_id: int | None
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class CartPricingResponse(BaseModel):
    items: list[CartItemPriceResponse]
    subtotal: Decimal
    discount: Decimal
    shipping_cost: Decimal
    tax: Decimal
    total: Decimal


CartPriceRequest = CartPricingRequest
CartPriceResponse = CartPricingResponse