from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from app.services.brand_service import create_brand, get_brand, list_brands, update_brand, deactivate_brand


router = APIRouter(prefix="/api/v1/brands", tags=["Brands"])


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def add_brand(payload: BrandCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return create_brand(db, payload.model_dump())


@router.get("/", response_model=list[BrandResponse])
def get_brands(search: str | None = None, active_only: bool = True, db: Session = Depends(get_db)):
    return list_brands(db, search, active_only)


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand_by_id(brand_id: int, db: Session = Depends(get_db)):
    return get_brand(db, brand_id)


@router.patch("/{brand_id}", response_model=BrandResponse)
def edit_brand(brand_id: int, payload: BrandUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return update_brand(db, brand_id, payload.model_dump(exclude_unset=True))


@router.delete("/{brand_id}")
def remove_brand(brand_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return deactivate_brand(db, brand_id)