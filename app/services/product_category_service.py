import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.product_category import ProductCategory


def generate_slug(name: str):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "category"


def unique_slug(db: Session, name: str, exclude_id: int | None = None):
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1

    while True:
        query = select(ProductCategory).where(ProductCategory.slug == slug)
        if exclude_id is not None:
            query = query.where(ProductCategory.id != exclude_id)
        if not db.scalar(query):
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def validate_parent(db: Session, parent_id: int | None, category_id: int | None = None):
    if parent_id is None:
        return

    parent = db.get(ProductCategory, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent category not found")

    if category_id is not None:
        if parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")

        current = parent
        while current:
            if current.id == category_id:
                raise HTTPException(status_code=400, detail="Category hierarchy cannot contain a cycle")
            current = current.parent


def create_category(db: Session, data: dict):
    name = data["name"]
    duplicate = db.scalar(select(ProductCategory).where(func.lower(ProductCategory.name) == name.lower()))
    if duplicate:
        raise HTTPException(status_code=409, detail="Category name already exists")

    validate_parent(db, data.get("parent_id"))
    category = ProductCategory(**data, slug=unique_slug(db, name))
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_category(db: Session, category_id: int):
    category = db.get(ProductCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


def list_categories(db: Session, search: str | None = None, active_only: bool = False, parent_id: int | None = None):
    query = select(ProductCategory)
    if search:
        query = query.where(ProductCategory.name.ilike(f"%{search}%"))
    if active_only:
        query = query.where(ProductCategory.is_active == True)
    if parent_id is not None:
        query = query.where(ProductCategory.parent_id == parent_id)
    return db.scalars(query.order_by(ProductCategory.name.asc())).all()


def update_category(db: Session, category_id: int, data: dict):
    category = get_category(db, category_id)

    if "name" in data and data["name"] is not None:
        duplicate = db.scalar(select(ProductCategory).where(func.lower(ProductCategory.name) == data["name"].lower(), ProductCategory.id != category_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Category name already exists")
        category.slug = unique_slug(db, data["name"], category_id)

    if "parent_id" in data:
        validate_parent(db, data["parent_id"], category_id)

    for key, value in data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int):
    category = get_category(db, category_id)
    child = db.scalar(select(ProductCategory).where(ProductCategory.parent_id == category_id))
    if child:
        raise HTTPException(status_code=409, detail="Move or delete child categories before deleting this category")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


def build_category_tree(categories: list[ProductCategory]):
    category_map = {category.id: {"id": category.id, "name": category.name, "slug": category.slug, "description": category.description, "parent_id": category.parent_id, "is_active": category.is_active, "children": []} for category in categories}
    roots = []

    for category in categories:
        node = category_map[category.id]
        if category.parent_id and category.parent_id in category_map:
            category_map[category.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def get_category_tree(db: Session):
    categories = db.scalars(select(ProductCategory).order_by(ProductCategory.name.asc())).all()
    return build_category_tree(categories)