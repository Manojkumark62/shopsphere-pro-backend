from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import create_product, get_product, list_products, update_product, archive_product


router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_product(payload: ProductCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return create_product(db, payload.model_dump())


@router.get("/", response_model=list[ProductResponse])
def get_products(search: str | None = None, category_id: int | None = None, brand_id: int | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return list_products(db, search, category_id, brand_id, page, page_size, True)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    return get_product(db, product_id, public_only=True)


@router.patch("/{product_id}", response_model=ProductResponse)
def edit_product(product_id: int, payload: ProductUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return update_product(db, product_id, payload.model_dump(exclude_unset=True))


@router.delete("/{product_id}")
def remove_product(product_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return archive_product(db, product_id)