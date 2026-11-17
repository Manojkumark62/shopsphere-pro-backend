
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.schemas.product_attribute import ProductAttributeCreate, CategoryAttributeCreate, ProductAttributeValueCreate
from app.services.product_attribute_service import create_attribute, list_attributes, assign_attribute_to_category, assign_product_attribute, list_product_attributes, filter_products_by_attribute, get_category_attributes

router = APIRouter(prefix="/api/v1", tags=["Product Attributes"])

@router.post("/attributes")
def create_new_attribute(data: ProductAttributeCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    return create_attribute(db, data)

@router.get("/attributes")
def get_attributes(db: Session = Depends(get_db)):
    return list_attributes(db)

@router.post("/categories/{category_id}/attributes")
def add_category_attribute(category_id: int, data: CategoryAttributeCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    return assign_attribute_to_category(db, category_id, data)

@router.get("/categories/{category_id}/attributes")
def get_attributes_for_category(category_id: int, db: Session = Depends(get_db)):
    rows = get_category_attributes(db, category_id)
    return [{"id": attribute.id, "name": attribute.name, "code": attribute.code, "data_type": attribute.data_type, "allowed_values": attribute.allowed_values.split(",") if attribute.allowed_values else None, "is_required": required} for attribute, required in rows]

@router.post("/products/{product_id}/attributes")
def add_product_attribute(product_id: int, data: ProductAttributeValueCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    return assign_product_attribute(db, product_id, data)

@router.get("/products/{product_id}/attributes")
def get_product_attributes(product_id: int, db: Session = Depends(get_db)):
    return list_product_attributes(db, product_id)

@router.get("/products/filter/by-attribute")
def filter_products(attribute_id: int, value: str, db: Session = Depends(get_db)):
    return filter_products_by_attribute(db, attribute_id, value)
