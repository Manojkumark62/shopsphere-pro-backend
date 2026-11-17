from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.auth import User
from app.schemas.cart_pricing import CartPricingRequest, CartPricingResponse
from app.services.cart_pricing_service import calculate_cart_price

router = APIRouter(prefix="/api/v1/cart", tags=["Cart Price Calculation"])


@router.post("/calculate", response_model=CartPricingResponse)
def calculate_cart_total(data: CartPricingRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return calculate_cart_price(db, current_user.id, data)
