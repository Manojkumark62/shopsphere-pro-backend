from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.product_variant import ProductVariant
from app.models.product import Product, ProductStatus


def get_product_or_404(db: Session, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def get_variant_or_404(db: Session, variant_id: int):
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Product variant not found")
    return variant


def create_variant(db: Session, product_id: int, data: dict):
    product = get_product_or_404(db, product_id)
    if product.status in [ProductStatus.INACTIVE, ProductStatus.ARCHIVED]:
        raise HTTPException(status_code=400, detail="Cannot add variants to an inactive or archived product")

    duplicate = db.scalar(select(ProductVariant).where(func.lower(ProductVariant.sku) == data["sku"].lower()))
    if duplicate:
        raise HTTPException(status_code=409, detail="Variant SKU already exists")

    variant = ProductVariant(product_id=product_id, **data)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def list_variants(db: Session, product_id: int, active_only: bool = True):
    get_product_or_404(db, product_id)
    query = select(ProductVariant).where(ProductVariant.product_id == product_id)
    if active_only:
        query = query.where(ProductVariant.is_active == True)
    return db.scalars(query.order_by(ProductVariant.id.desc())).all()


def get_variant(db: Session, variant_id: int):
    return get_variant_or_404(db, variant_id)


def update_variant(db: Session, variant_id: int, data: dict):
    variant = get_variant_or_404(db, variant_id)

    if data.get("sku") is not None:
        duplicate = db.scalar(select(ProductVariant).where(func.lower(ProductVariant.sku) == data["sku"].lower(), ProductVariant.id != variant_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Variant SKU already exists")

    for key, value in data.items():
        setattr(variant, key, value)

    db.commit()
    db.refresh(variant)
    return variant


def deactivate_variant(db: Session, variant_id: int):
    variant = get_variant_or_404(db, variant_id)
    variant.is_active = False
    db.commit()
    return {"message": "Product variant deactivated successfully"}