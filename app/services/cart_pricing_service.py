
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.cart import ShoppingCart, CartItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_pricing import ProductPrice
from app.schemas.cart_pricing import CartPriceRequest, CartItemPriceResponse, CartPriceResponse
from app.services.coupon_service import calculate_coupon_discount

CENT = Decimal("0.01")

def money(value):
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)

def get_current_unit_price(db: Session, product: Product, variant: ProductVariant | None = None) -> Decimal:
    now = datetime.utcnow()
    query = select(ProductPrice).where(ProductPrice.product_id == product.id, ProductPrice.is_active.is_(True), ProductPrice.valid_from <= now, (ProductPrice.valid_until.is_(None)) | (ProductPrice.valid_until > now))
    query = query.where(ProductPrice.variant_id == variant.id) if variant else query.where(ProductPrice.variant_id.is_(None))
    price_record = db.scalar(query.order_by(ProductPrice.valid_from.desc()).limit(1))
    if price_record:
        return money(price_record.sale_price if price_record.sale_price is not None else price_record.base_price)
    if variant and variant.price is not None:
        return money(variant.price)
    return money(product.base_price)

def calculate_cart_price(db: Session, customer_id: int, data: CartPriceRequest):
    cart = db.scalar(select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.is_active.is_(True)))
    if not cart:
        raise HTTPException(status_code=404, detail="Active cart not found")

    cart_items = db.scalars(select(CartItem).where(CartItem.cart_id == cart.id)).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    items_response = []
    subtotal = Decimal("0.00")

    for item in cart_items:
        product = db.get(Product, item.product_id)
        if not product or str(product.status).lower().split(".")[-1] != "active":
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} is unavailable")

        variant = db.get(ProductVariant, item.variant_id) if item.variant_id else None
        if item.variant_id and (not variant or variant.product_id != product.id or not variant.is_active):
            raise HTTPException(status_code=400, detail=f"Product variant {item.variant_id} is unavailable")

        unit_price = get_current_unit_price(db, product, variant)
        item_subtotal = money(unit_price * item.quantity)
        subtotal += item_subtotal
        items_response.append(CartItemPriceResponse(cart_item_id=item.id, product_id=product.id, variant_id=item.variant_id, product_name=product.name, quantity=item.quantity, unit_price=unit_price, subtotal=item_subtotal))

    subtotal = money(subtotal)
    discount = Decimal("0.00")
    if data.coupon_code:
        discount = money(calculate_coupon_discount(db, customer_id, data.coupon_code, subtotal))
    discount = min(discount, subtotal)

    shipping_cost = money(data.shipping_cost)
    if shipping_cost < 0:
        raise HTTPException(status_code=400, detail="Shipping cost cannot be negative")

    tax_rate = Decimal(str(data.tax_rate))
    if tax_rate < 0:
        raise HTTPException(status_code=400, detail="Tax rate cannot be negative")

    taxable_amount = money(subtotal - discount)
    tax = money(taxable_amount * tax_rate)
    total = money(taxable_amount + tax + shipping_cost)

    return CartPriceResponse(items=items_response, subtotal=subtotal, discount=discount, shipping_cost=shipping_cost, tax=tax, total=total)
