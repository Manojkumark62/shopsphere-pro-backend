
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseStockCreate, WarehouseResponse, WarehouseStockResponse
from app.services.warehouse_service import create_warehouse, list_warehouses, update_warehouse, set_warehouse_stock, list_warehouse_stock, get_product_warehouse_stock, get_warehouse_or_404, get_warehouse_usage

router = APIRouter(prefix="/api/v1", tags=["Warehouse Management"])

@router.post("/warehouses", response_model=WarehouseResponse)
def add_warehouse(data: WarehouseCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return create_warehouse(db, data)

@router.get("/warehouses", response_model=list[WarehouseResponse])
def get_warehouses(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "employee"))):
    return list_warehouses(db, active_only=True)

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "employee"))):
    return get_warehouse_or_404(db, warehouse_id)

@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def edit_warehouse(warehouse_id: int, data: WarehouseUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return update_warehouse(db, warehouse_id, data)

@router.get("/warehouses/{warehouse_id}/capacity")
def warehouse_capacity(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "employee"))):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    used = get_warehouse_usage(db, warehouse_id)
    return {"warehouse_id": warehouse.id, "warehouse_name": warehouse.name, "capacity_units": warehouse.capacity_units, "used_units": used, "available_capacity": warehouse.capacity_units - used}

@router.put("/warehouses/{warehouse_id}/inventory", response_model=WarehouseStockResponse)
def update_warehouse_inventory(warehouse_id: int, data: WarehouseStockCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return set_warehouse_stock(db, warehouse_id, data)

@router.get("/warehouses/{warehouse_id}/inventory", response_model=list[WarehouseStockResponse])
def get_warehouse_inventory(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "employee"))):
    return list_warehouse_stock(db, warehouse_id)

@router.get("/products/{product_id}/warehouses", response_model=list[WarehouseStockResponse])
def get_product_stock_by_warehouse(product_id: int, variant_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "employee"))):
    return get_product_warehouse_stock(db, product_id, variant_id)
