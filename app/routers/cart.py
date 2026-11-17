from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.auth import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse, ShoppingCartResponse, CartAvailabilityResponse
from app.services.cart_service import add_cart_item, update_cart_item, remove_cart_item, get_cart_items, clear_cart, check_cart_availability

router = APIRouter(prefix="/api/v1/cart", tags=["Shopping Cart"])


@router.get("/", response_model=ShoppingCartResponse)
def retrieve_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_cart_items(db, current_user.id)


@router.post("/items", response_model=CartItemResponse, status_code=201)
def add_item(data: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return add_cart_item(db, current_user.id, data)


@router.patch("/items/{item_id}", response_model=CartItemResponse)
def update_item(item_id: int, data: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return update_cart_item(db, current_user.id, item_id, data.quantity)


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return remove_cart_item(db, current_user.id, item_id)


@router.delete("/clear")
def delete_cart_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return clear_cart(db, current_user.id)


@router.get("/availability", response_model=list[CartAvailabilityResponse])
def cart_availability(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return check_cart_availability(db, current_user.id)