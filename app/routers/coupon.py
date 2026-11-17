from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponResponse
from app.services.coupon_service import create_coupon, list_coupons, get_coupon_or_404, update_coupon, set_coupon_active

router = APIRouter(prefix="/api/v1/coupons", tags=["Coupon Management"])

@router.post("/", response_model=CouponResponse, status_code=201, dependencies=[Depends(require_roles("admin"))])
def create_coupon_endpoint(data: CouponCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return create_coupon(db, data, current_user.id)

@router.get("/", response_model=list[CouponResponse], dependencies=[Depends(require_roles("admin"))])
def list_coupons_endpoint(active_only: bool = Query(False), db: Session = Depends(get_db)):
    return list_coupons(db, active_only)

@router.get("/{coupon_id}", response_model=CouponResponse, dependencies=[Depends(require_roles("admin"))])
def get_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    return get_coupon_or_404(db, coupon_id)

@router.patch("/{coupon_id}", response_model=CouponResponse, dependencies=[Depends(require_roles("admin"))])
def update_coupon_endpoint(coupon_id: int, data: CouponUpdate, db: Session = Depends(get_db)):
    return update_coupon(db, coupon_id, data)

@router.patch("/{coupon_id}/activate", response_model=CouponResponse, dependencies=[Depends(require_roles("admin"))])
def activate_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    return set_coupon_active(db, coupon_id, True)

@router.patch("/{coupon_id}/deactivate", response_model=CouponResponse, dependencies=[Depends(require_roles("admin"))])
def deactivate_coupon_endpoint(coupon_id: int, db: Session = Depends(get_db)):
    return set_coupon_active(db, coupon_id, False)