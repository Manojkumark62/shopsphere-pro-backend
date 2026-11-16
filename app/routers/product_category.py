from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse
from app.services.product_category_service import create_category, get_category, list_categories, update_category, delete_category, get_category_tree


router = APIRouter(prefix="/api/v1/categories", tags=["Product Categories"])


@router.post("/", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def add_category(payload: ProductCategoryCreate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return create_category(db, payload.model_dump())


@router.get("/", response_model=list[ProductCategoryResponse])
def get_categories(search: str | None = None, active_only: bool = False, parent_id: int | None = None, db: Session = Depends(get_db)):
    return list_categories(db, search, active_only, parent_id)


@router.get("/tree")
def get_categories_tree(db: Session = Depends(get_db)):
    return get_category_tree(db)


@router.get("/{category_id}", response_model=ProductCategoryResponse)
def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    return get_category(db, category_id)


@router.patch("/{category_id}", response_model=ProductCategoryResponse)
def edit_category(category_id: int, payload: ProductCategoryUpdate, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return update_category(db, category_id, payload.model_dump(exclude_unset=True))


@router.delete("/{category_id}")
def remove_category(category_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return delete_category(db, category_id)