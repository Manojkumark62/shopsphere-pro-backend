
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.inventory import InventoryAdjustment, InventoryReservation, InventoryMovementResponse
from app.services.inventory_service import add_stock, reduce_stock, reserve_stock, release_stock, fulfill_reserved_stock, get_inventory, get_inventory_movements

router = APIRouter(prefix="/api/v1", tags=["Inventory Management"])

@router.post("/products/{product_id}/inventory/stock-in")
def stock_in(product_id: int, data: InventoryAdjustment, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return add_stock(db, product_id, variant_id, data.quantity, data.reason, current_user.id)

@router.post("/products/{product_id}/inventory/stock-out")
def stock_out(product_id: int, data: InventoryAdjustment, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return reduce_stock(db, product_id, variant_id, data.quantity, data.reason, current_user.id)

@router.post("/products/{product_id}/inventory/reserve")
def reserve(product_id: int, data: InventoryReservation, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return reserve_stock(db, product_id, variant_id, data.quantity, data.reason, current_user.id)

@router.post("/products/{product_id}/inventory/release")
def release(product_id: int, data: InventoryReservation, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return release_stock(db, product_id, variant_id, data.quantity, data.reason, current_user.id)

@router.post("/products/{product_id}/inventory/fulfill")
def fulfill(product_id: int, data: InventoryReservation, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return fulfill_reserved_stock(db, product_id, variant_id, data.quantity, data.reason, current_user.id)

@router.get("/products/{product_id}/inventory")
def inventory_details(product_id: int, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return get_inventory(db, product_id, variant_id)

@router.get("/products/{product_id}/inventory/movements", response_model=list[InventoryMovementResponse])
def inventory_history(product_id: int, variant_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return get_inventory_movements(db, product_id, variant_id)
