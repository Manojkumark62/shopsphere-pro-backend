
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_pricing import ProductPrice

def validate_product_and_variant(db: Session, product_id: int, variant_id: int | None):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id:
            raise HTTPException(status_code=400, detail="Variant does not belong to this product")
        if not variant.is_active:
            raise HTTPException(status_code=400, detail="Variant is inactive")
    return product

def create_product_price(db: Session, product_id: int, data, user_id: int):
    validate_product_and_variant(db, product_id, data.variant_id)
    start = data.valid_from
    end = data.valid_until
    conditions = [ProductPrice.product_id == product_id, ProductPrice.is_active.is_(True), ProductPrice.valid_from < (end or datetime.max), or_(ProductPrice.valid_until.is_(None), ProductPrice.valid_until > start)]
    if data.variant_id is None:
        conditions.append(ProductPrice.variant_id.is_(None))
    else:
        conditions.append(ProductPrice.variant_id == data.variant_id)
    overlapping = db.scalar(select(ProductPrice).where(*conditions).limit(1))
    if overlapping:
        raise HTTPException(status_code=409, detail="This pricing period overlaps an existing active price")
    record = ProductPrice(product_id=product_id, variant_id=data.variant_id, base_price=data.base_price, sale_price=data.sale_price, valid_from=start, valid_until=end, created_by=user_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_current_product_price(db: Session, product_id: int, variant_id: int | None = None):
    product = validate_product_and_variant(db, product_id, variant_id)
    now = datetime.utcnow()
    statement = select(ProductPrice).where(ProductPrice.product_id == product_id, ProductPrice.is_active.is_(True), ProductPrice.valid_from <= now, or_(ProductPrice.valid_until.is_(None), ProductPrice.valid_until > now))
    if variant_id is None:
        statement = statement.where(ProductPrice.variant_id.is_(None))
    else:
        statement = statement.where(ProductPrice.variant_id == variant_id)
    record = db.scalar(statement.order_by(ProductPrice.valid_from.desc()).limit(1))
    if record:
        base_price = record.base_price
        sale_price = record.sale_price
        record_id = record.id
    elif variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        base_price = variant.price
        sale_price = variant.compare_at_price if variant.compare_at_price and variant.compare_at_price < variant.price else None
        record_id = None
    else:
        base_price = product.base_price
        sale_price = product.compare_at_price if product.compare_at_price and product.compare_at_price < product.base_price else None
        record_id = None
    effective_price = sale_price if sale_price is not None else base_price
    return {"product_id": product_id, "variant_id": variant_id, "base_price": base_price, "sale_price": sale_price, "effective_price": effective_price, "is_on_sale": sale_price is not None, "price_record_id": record_id}

def get_product_price_history(db: Session, product_id: int, variant_id: int | None = None):
    validate_product_and_variant(db, product_id, variant_id)
    statement = select(ProductPrice).where(ProductPrice.product_id == product_id)
    if variant_id is None:
        statement = statement.where(ProductPrice.variant_id.is_(None))
    else:
        statement = statement.where(ProductPrice.variant_id == variant_id)
    return db.scalars(statement.order_by(ProductPrice.created_at.desc())).all()

def deactivate_product_price(db: Session, price_id: int):
    record = db.get(ProductPrice, price_id)
    if not record:
        raise HTTPException(status_code=404, detail="Price record not found")
    if not record.is_active:
        raise HTTPException(status_code=400, detail="Price record is already inactive")
    record.is_active = False
    db.commit()
    db.refresh(record)
    return record
