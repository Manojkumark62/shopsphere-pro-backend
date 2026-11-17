from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.cart import ShoppingCart, CartItem
from app.models.product import Product, ProductStatus
from app.models.product_variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseStatus
from app.models.warehouse_inventory import WarehouseInventory


def get_or_create_cart(db: Session, customer_id: int):
    cart = db.scalar(select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.is_active.is_(True)))
    if cart:
        return cart
    cart = ShoppingCart(customer_id=customer_id, is_active=True)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def get_customer_cart(db: Session, customer_id: int):
    cart = db.scalar(select(ShoppingCart).where(ShoppingCart.customer_id == customer_id, ShoppingCart.is_active.is_(True)))
    if not cart:
        cart = get_or_create_cart(db, customer_id)
    return cart


def validate_product(db: Session, product_id: int, variant_id: int | None):
    product = db.get(Product, product_id)
    if not product or product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active product not found")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id or not variant.is_active:
            raise HTTPException(status_code=400, detail="Invalid or inactive product variant")
    return product


def get_available_quantity(db: Session, product_id: int, variant_id: int | None):
    statement = select(func.coalesce(func.sum(WarehouseInventory.quantity), 0)).join(Warehouse, Warehouse.id == WarehouseInventory.warehouse_id).where(WarehouseInventory.product_id == product_id, WarehouseInventory.variant_id == variant_id, Warehouse.status == WarehouseStatus.ACTIVE)
    return int(db.scalar(statement) or 0)


def add_cart_item(db: Session, customer_id: int, data):
    try:
        validate_product(db, data.product_id, data.variant_id)
        cart = get_customer_cart(db, customer_id)
        available = get_available_quantity(db, data.product_id, data.variant_id)
        existing = db.scalar(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id, CartItem.variant_id == data.variant_id).with_for_update())
        requested_total = data.quantity + (existing.quantity if existing else 0)
        if requested_total > available:
            raise HTTPException(status_code=400, detail=f"Only {available} units are available")
        if existing:
            existing.quantity = requested_total
            existing.updated_at = datetime.utcnow()
            item = existing
        else:
            item = CartItem(cart_id=cart.id, product_id=data.product_id, variant_id=data.variant_id, quantity=data.quantity)
            db.add(item)
        cart.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise


def update_cart_item(db: Session, customer_id: int, item_id: int, quantity: int):
    try:
        cart = get_customer_cart(db, customer_id)
        item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id).with_for_update())
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        available = get_available_quantity(db, item.product_id, item.variant_id)
        if quantity > available:
            raise HTTPException(status_code=400, detail=f"Only {available} units are available")
        item.quantity = quantity
        item.updated_at = datetime.utcnow()
        cart.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise


def remove_cart_item(db: Session, customer_id: int, item_id: int):
    cart = get_customer_cart(db, customer_id)
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    cart.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Cart item removed successfully"}


def get_cart_items(db: Session, customer_id: int):
    cart = get_customer_cart(db, customer_id)
    return cart


def clear_cart(db: Session, customer_id: int):
    cart = get_customer_cart(db, customer_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    cart.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Shopping cart cleared successfully"}


def check_cart_availability(db: Session, customer_id: int):
    cart = get_customer_cart(db, customer_id)
    results = []
    for item in cart.items:
        available = get_available_quantity(db, item.product_id, item.variant_id)
        results.append({"product_id": item.product_id, "variant_id": item.variant_id, "requested_quantity": item.quantity, "available_quantity": available, "is_available": item.quantity <= available})
    return results