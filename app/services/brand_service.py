import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.brand import Brand


def generate_slug(name: str):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "brand"


def create_unique_slug(db: Session, name: str, exclude_id: int | None = None):
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1

    while True:
        query = select(Brand).where(Brand.slug == slug)
        if exclude_id is not None:
            query = query.where(Brand.id != exclude_id)
        if not db.scalar(query):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def get_brand(db: Session, brand_id: int):
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


def create_brand(db: Session, data: dict):
    name = data["name"]
    duplicate = db.scalar(select(Brand).where(func.lower(Brand.name) == name.lower()))
    if duplicate:
        raise HTTPException(status_code=409, detail="Brand already exists")

    data["logo_url"] = str(data["logo_url"]) if data.get("logo_url") else None
    brand = Brand(**data, slug=create_unique_slug(db, name))
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def list_brands(db: Session, search: str | None = None, active_only: bool = False):
    query = select(Brand)
    if search:
        query = query.where(Brand.name.ilike(f"%{search}%"))
    if active_only:
        query = query.where(Brand.is_active == True)
    return db.scalars(query.order_by(Brand.name.asc())).all()


def update_brand(db: Session, brand_id: int, data: dict):
    brand = get_brand(db, brand_id)

    if data.get("name") is not None:
        duplicate = db.scalar(select(Brand).where(func.lower(Brand.name) == data["name"].lower(), Brand.id != brand_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Brand name already exists")
        brand.slug = create_unique_slug(db, data["name"], brand_id)

    if "logo_url" in data and data["logo_url"] is not None:
        data["logo_url"] = str(data["logo_url"])

    for key, value in data.items():
        setattr(brand, key, value)

    db.commit()
    db.refresh(brand)
    return brand


def deactivate_brand(db: Session, brand_id: int):
    brand = get_brand(db, brand_id)
    brand.is_active = False
    db.commit()
    return {"message": "Brand deactivated successfully"}