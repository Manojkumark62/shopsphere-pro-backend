import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.product import Product, ProductStatus
from app.models.product_category import ProductCategory
from app.models.brand import Brand


def generate_slug(name: str):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "product"


def create_unique_slug(db: Session, name: str, exclude_id: int | None = None):
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1

    while True:
        query = select(Product).where(Product.slug == slug)
        if exclude_id is not None:
            query = query.where(Product.id != exclude_id)
        if not db.scalar(query):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def validate_category_and_brand(db: Session, category_id: int, brand_id: int):
    category = db.get(ProductCategory, category_id)
    brand = db.get(Brand, brand_id)

    if not category or not category.is_active:
        raise HTTPException(status_code=400, detail="Category does not exist or is inactive")
    if not brand or not brand.is_active:
        raise HTTPException(status_code=400, detail="Brand does not exist or is inactive")


def create_product(db: Session, data: dict):
    duplicate = db.scalar(select(Product).where(func.lower(Product.sku) == data["sku"].lower()))
    if duplicate:
        raise HTTPException(status_code=409, detail="Product SKU already exists")

    validate_category_and_brand(db, data["category_id"], data["brand_id"])
    product = Product(**data, slug=create_unique_slug(db, data["name"]))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product(db: Session, product_id: int, public_only: bool = False):
    product = db.get(Product, product_id)
    if not product or (public_only and product.status != ProductStatus.ACTIVE):
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def list_products(db: Session, search: str | None = None, category_id: int | None = None, brand_id: int | None = None, page: int = 1, page_size: int = 20, public_only: bool = True):
    query = select(Product)

    if public_only:
        query = query.where(Product.status == ProductStatus.ACTIVE)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    if brand_id is not None:
        query = query.where(Product.brand_id == brand_id)

    return db.scalars(query.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()


def update_product(db: Session, product_id: int, data: dict):
    product = get_product(db, product_id)

    if data.get("sku") is not None:
        duplicate = db.scalar(select(Product).where(func.lower(Product.sku) == data["sku"].lower(), Product.id != product_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Product SKU already exists")

    category_id = data.get("category_id", product.category_id)
    brand_id = data.get("brand_id", product.brand_id)
    validate_category_and_brand(db, category_id, brand_id)

    new_name = data.get("name")
    if new_name is not None:
        product.slug = create_unique_slug(db, new_name, product_id)

    for key, value in data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


def archive_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    product.status = ProductStatus.ARCHIVED
    db.commit()
    return {"message": "Product archived successfully"}