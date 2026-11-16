
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User, UserRole
from app.schemas.user_management import UserCreate, UserUpdate, UserStatusUpdate, UserResponse, UserActivityResponse
from app.services.user_service import create_user, update_user, update_user_status, search_users, get_user_activities

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])

@router.post("/", response_model=UserResponse, status_code=201)
def create_new_user(data: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    return create_user(db, data, admin)

@router.get("/", response_model=list[UserResponse])
def list_users(search: str | None = None, role: UserRole | None = None, is_active: bool | None = None, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    return search_users(db, search, role, is_active, skip, limit)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    from app.services.user_service import get_user_or_404
    return get_user_or_404(db, user_id)

@router.patch("/{user_id}", response_model=UserResponse)
def edit_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    return update_user(db, user_id, data, admin)

@router.patch("/{user_id}/status", response_model=UserResponse)
def change_user_status(user_id: int, data: UserStatusUpdate, db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    return update_user_status(db, user_id, data.is_active, admin)

@router.get("/{user_id}/activities", response_model=list[UserActivityResponse])
def user_activities(user_id: int, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), admin: User = Depends(require_roles("admin"))):
    return get_user_activities(db, user_id, skip, limit)
