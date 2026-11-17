from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.auth import User
from app.schemas.wishlist import WishlistItemCreate, WishlistItemResponse, WishlistAvailabilityResponse
from app.services.wishlist_service import add_wishlist_item, get_wishlist, remove_wishlist_item, remove_product_from_wishlist, check_wishlist_availability, clear_wishlist

router = APIRouter(prefix="/api/v1/wishlist", tags=["Wishlist Management"])


@router.post("/items", response_model=WishlistItemResponse, status_code=201)
def add_item(data: WishlistItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return add_wishlist_item(db, current_user.id, data)


@router.get("/", response_model=list[WishlistItemResponse])
def retrieve_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_wishlist(db, current_user.id)


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return remove_wishlist_item(db, current_user.id, item_id)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return remove_product_from_wishlist(db, current_user.id, product_id, variant_id)


@router.get("/availability", response_model=list[WishlistAvailabilityResponse])
def wishlist_availability(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return check_wishlist_availability(db, current_user.id)


@router.delete("/clear")
def delete_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return clear_wishlist(db, current_user.id)