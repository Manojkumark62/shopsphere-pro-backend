from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.product_variant import ProductVariantCreate, ProductVariantUpdate, ProductVariantResponse
from app.services.product_variant_service import create_variant, list_variants, get_variant, update_variant, deactivate_variant


router = APIRouter(tags=["Product Variants"])


@router.post("/api/v1/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def add_variant(product_id: int, payload: ProductVariantCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return create_variant(db, product_id, payload.model_dump())


@router.get("/api/v1/products/{product_id}/variants", response_model=list[ProductVariantResponse])
def get_product_variants(product_id: int, active_only: bool = True, db: Session = Depends(get_db)):
    return list_variants(db, product_id, active_only)


@router.get("/api/v1/variants/{variant_id}", response_model=ProductVariantResponse)
def get_variant_by_id(variant_id: int, db: Session = Depends(get_db)):
    return get_variant(db, variant_id)


@router.patch("/api/v1/variants/{variant_id}", response_model=ProductVariantResponse)
def edit_variant(variant_id: int, payload: ProductVariantUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return update_variant(db, variant_id, payload.model_dump(exclude_unset=True))


@router.delete("/api/v1/variants/{variant_id}")
def remove_variant(variant_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return deactivate_variant(db, variant_id)