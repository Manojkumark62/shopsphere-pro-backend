
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.models.product_attribute import ProductAttribute, CategoryAttribute, ProductAttributeValue
from app.models.product import Product
from app.models.product_category import ProductCategory


def get_category_hierarchy_ids(db: Session, category_id: int):
    ids = []
    current_id = category_id
    seen = set()
    while current_id is not None and current_id not in seen:
        seen.add(current_id)
        ids.append(current_id)
        category = db.get(ProductCategory, current_id)
        current_id = category.parent_id if category else None
    return ids

def get_attribute_or_404(db: Session, attribute_id: int):
    attribute = db.get(ProductAttribute, attribute_id)
    if not attribute or not attribute.is_active:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return attribute

def create_attribute(db: Session, data):
    code = data.code.strip().lower()
    name = data.name.strip()
    existing = db.scalar(select(ProductAttribute).where((ProductAttribute.code == code) | (ProductAttribute.name == name)))
    if existing:
        raise HTTPException(status_code=409, detail="Attribute name or code already exists")
    attribute = ProductAttribute(name=name, code=code, data_type=data.data_type, allowed_values=",".join(data.allowed_values) if data.allowed_values else None)
    db.add(attribute)
    db.commit()
    db.refresh(attribute)
    return attribute

def list_attributes(db: Session):
    return db.scalars(select(ProductAttribute).where(ProductAttribute.is_active.is_(True)).order_by(ProductAttribute.name)).all()

def assign_attribute_to_category(db: Session, category_id: int, data):
    from app.models.product_category import ProductCategory
    category = db.get(ProductCategory, category_id)
    if not category or not category.is_active:
        raise HTTPException(status_code=404, detail="Active category not found")
    attribute = get_attribute_or_404(db, data.attribute_id)
    existing = db.scalar(select(CategoryAttribute).where(CategoryAttribute.category_id == category_id, CategoryAttribute.attribute_id == data.attribute_id))
    if existing:
        raise HTTPException(status_code=409, detail="Attribute already assigned to category")
    assignment = CategoryAttribute(category_id=category_id, attribute_id=attribute.id, is_required=data.is_required)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

def validate_attribute_value(attribute: ProductAttribute, value: str):
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="Attribute value cannot be empty")
    if attribute.data_type == "number":
        try:
            float(value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"{attribute.name} must be numeric")
    elif attribute.data_type == "boolean":
        if value.lower() not in ["true", "false"]:
            raise HTTPException(status_code=400, detail=f"{attribute.name} must be true or false")
    if attribute.allowed_values:
        allowed = [item.strip().casefold() for item in attribute.allowed_values.split(",")]
        if value.casefold() not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid value for {attribute.name}")
    return value

def assign_product_attribute(db: Session, product_id: int, data):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    attribute = get_attribute_or_404(db, data.attribute_id)
    category_ids = get_category_hierarchy_ids(db, product.category_id)
    category_assignment = db.scalar(
        select(CategoryAttribute).where(
            CategoryAttribute.category_id.in_(category_ids),
            CategoryAttribute.attribute_id == attribute.id,
        )
    )
    if not category_assignment:
        raise HTTPException(status_code=400, detail="Attribute is not configured for this product category")
    value = validate_attribute_value(attribute, data.value)
    existing = db.scalar(select(ProductAttributeValue).where(ProductAttributeValue.product_id == product_id, ProductAttributeValue.attribute_id == attribute.id))
    if existing:
        existing.value = value
        db.commit()
        db.refresh(existing)
        return existing
    record = ProductAttributeValue(product_id=product_id, attribute_id=attribute.id, value=value)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def list_product_attributes(db: Session, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db.scalars(select(ProductAttributeValue).where(ProductAttributeValue.product_id == product_id)).all()

def filter_products_by_attribute(db: Session, attribute_id: int, value: str):
    attribute = get_attribute_or_404(db, attribute_id)
    validated_value = validate_attribute_value(attribute, value)
    statement = select(Product).join(ProductAttributeValue, Product.id == ProductAttributeValue.product_id).where(ProductAttributeValue.attribute_id == attribute_id, ProductAttributeValue.value == validated_value)
    return db.scalars(statement).all()

def get_category_attributes(db: Session, category_id: int):
    category_ids = get_category_hierarchy_ids(db, category_id)
    statement = (
        select(ProductAttribute, CategoryAttribute.is_required)
        .join(CategoryAttribute, ProductAttribute.id == CategoryAttribute.attribute_id)
        .where(CategoryAttribute.category_id.in_(category_ids), ProductAttribute.is_active.is_(True))
        .distinct()
    )
    return db.execute(statement).all()
