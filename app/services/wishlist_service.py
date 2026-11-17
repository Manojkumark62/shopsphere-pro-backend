from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.wishlist import WishlistItem
from app.models.product import Product, ProductStatus
from app.models.product_variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseStatus
from app.models.warehouse_inventory import WarehouseInventory


def validate_wishlist_product(db: Session, product_id: int, variant_id: int | None):
    product = db.get(Product, product_id)

    if not product or product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active product not found")

    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)

        if not variant or variant.product_id != product_id or not variant.is_active:
            raise HTTPException(status_code=400, detail="Invalid or inactive product variant")


def add_wishlist_item(db: Session, customer_id: int, data):
    try:
        validate_wishlist_product(db, data.product_id, data.variant_id)

        existing = db.scalar(
            select(WishlistItem).where(
                WishlistItem.customer_id == customer_id,
                WishlistItem.product_id == data.product_id,
                WishlistItem.variant_id == data.variant_id,
            )
        )

        if existing:
            raise HTTPException(status_code=409, detail="Product already exists in wishlist")

        item = WishlistItem(customer_id=customer_id, product_id=data.product_id, variant_id=data.variant_id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product already exists in wishlist")
    except Exception:
        db.rollback()
        raise


def get_wishlist(db: Session, customer_id: int):
    statement = select(WishlistItem).where(WishlistItem.customer_id == customer_id).order_by(WishlistItem.created_at.desc())
    return db.scalars(statement).all()


def remove_wishlist_item(db: Session, customer_id: int, item_id: int):
    item = db.scalar(
        select(WishlistItem).where(
            WishlistItem.id == item_id,
            WishlistItem.customer_id == customer_id,
        )
    )

    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    db.delete(item)
    db.commit()
    return {"message": "Wishlist item removed successfully"}


def remove_product_from_wishlist(db: Session, customer_id: int, product_id: int, variant_id: int | None = None):
    item = db.scalar(
        select(WishlistItem).where(
            WishlistItem.customer_id == customer_id,
            WishlistItem.product_id == product_id,
            WishlistItem.variant_id == variant_id,
        )
    )

    if not item:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")

    db.delete(item)
    db.commit()
    return {"message": "Product removed from wishlist successfully"}


def get_available_quantity(db: Session, product_id: int, variant_id: int | None):
    statement = select(func.coalesce(func.sum(WarehouseInventory.quantity), 0)).join(
        Warehouse,
        Warehouse.id == WarehouseInventory.warehouse_id,
    ).where(
        WarehouseInventory.product_id == product_id,
        WarehouseInventory.variant_id == variant_id,
        Warehouse.status == WarehouseStatus.ACTIVE,
    )

    return int(db.scalar(statement) or 0)


def check_wishlist_availability(db: Session, customer_id: int):
    items = get_wishlist(db, customer_id)
    results = []

    for item in items:
        available = get_available_quantity(db, item.product_id, item.variant_id)
        product = db.get(Product, item.product_id)

        if item.variant_id is not None:
            variant = db.get(ProductVariant, item.variant_id)
            if not variant or not variant.is_active:
                available = 0

        if not product or product.status != ProductStatus.ACTIVE:
            available = 0

        results.append({
            "wishlist_item_id": item.id,
            "product_id": item.product_id,
            "variant_id": item.variant_id,
            "available_quantity": available,
            "is_available": available > 0,
        })

    return results


def clear_wishlist(db: Session, customer_id: int):
    db.query(WishlistItem).filter(WishlistItem.customer_id == customer_id).delete(synchronize_session=False)
    db.commit()
    return {"message": "Wishlist cleared successfully"}