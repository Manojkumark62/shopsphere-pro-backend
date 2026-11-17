from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.auth import User
from app.schemas.product_pricing import ProductPriceCreate, ProductPriceResponse
from app.services.product_pricing_service import create_product_price, get_current_product_price, get_product_price_history, deactivate_product_price

router = APIRouter(prefix="/api/v1/products", tags=["Product Pricing"])


@router.post("/{product_id}/prices", response_model=ProductPriceResponse, status_code=201)
def create_product_price_endpoint(
    product_id: int,
    data: ProductPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_product_price(db, product_id, data, current_user.id)


@router.get("/{product_id}/prices/current")
def get_product_price_endpoint(product_id: int, variant_id: int | None = None, db: Session = Depends(get_db)):
    return get_current_product_price(db, product_id, variant_id)


@router.get("/{product_id}/prices", response_model=list[ProductPriceResponse])
def list_product_price_history_endpoint(product_id: int, variant_id: int | None = None, db: Session = Depends(get_db)):
    return get_product_price_history(db, product_id, variant_id)


@router.patch("/prices/{price_id}/deactivate", response_model=ProductPriceResponse)
def deactivate_product_price_endpoint(price_id: int, db: Session = Depends(get_db)):
    return deactivate_product_price(db, price_id)
