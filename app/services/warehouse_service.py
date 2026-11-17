
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.warehouse import Warehouse, WarehouseStatus
from app.models.warehouse_inventory import WarehouseInventory
from app.models.product import Product
from app.models.product_variant import ProductVariant

def get_warehouse_or_404(db: Session, warehouse_id: int):
    warehouse = db.get(Warehouse, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

def get_warehouse_usage(db: Session, warehouse_id: int):
    return db.scalar(select(func.coalesce(func.sum(WarehouseInventory.quantity), 0)).where(WarehouseInventory.warehouse_id == warehouse_id)) or 0

def create_warehouse(db: Session, data):
    existing = db.scalar(select(Warehouse).where((Warehouse.code == data.code.strip().upper()) | (Warehouse.name == data.name.strip())))
    if existing:
        raise HTTPException(status_code=409, detail="Warehouse name or code already exists")
    warehouse = Warehouse(name=data.name.strip(), code=data.code.strip().upper(), address=data.address.strip(), city=data.city.strip(), state=data.state.strip(), country=data.country.strip(), postal_code=data.postal_code.strip(), capacity_units=data.capacity_units)
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse

def list_warehouses(db: Session, active_only: bool = False):
    statement = select(Warehouse)
    if active_only:
        statement = statement.where(Warehouse.status == WarehouseStatus.ACTIVE)
    return db.scalars(statement.order_by(Warehouse.name)).all()

def update_warehouse(db: Session, warehouse_id: int, data):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    updates = data.model_dump(exclude_unset=True)
    if "capacity_units" in updates and updates["capacity_units"] < get_warehouse_usage(db, warehouse_id):
        raise HTTPException(status_code=409, detail="Capacity cannot be lower than current stock")
    if updates.get("status") == "inactive" and get_warehouse_usage(db, warehouse_id) > 0:
        raise HTTPException(status_code=409, detail="Move warehouse stock before deactivating the warehouse")
    if "name" in updates and updates["name"]:
        duplicate = db.scalar(select(Warehouse).where(Warehouse.name == updates["name"].strip(), Warehouse.id != warehouse_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Warehouse name already exists")
        updates["name"] = updates["name"].strip()
    for key, value in updates.items():
        if key == "status":
            value = WarehouseStatus(value)
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse

def get_warehouse_stock_row(db: Session, warehouse_id: int, product_id: int, variant_id: int | None):
    statement = select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse_id, WarehouseInventory.product_id == product_id)
    statement = statement.where(WarehouseInventory.variant_id == variant_id) if variant_id is not None else statement.where(WarehouseInventory.variant_id.is_(None))
    return db.scalar(statement.with_for_update())

def set_warehouse_stock(db: Session, warehouse_id: int, data):
    try:
        warehouse = get_warehouse_or_404(db, warehouse_id)
        if warehouse.status != WarehouseStatus.ACTIVE:
            raise HTTPException(status_code=409, detail="Warehouse is not active")
        product = db.get(Product, data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if data.variant_id is not None:
            variant = db.get(ProductVariant, data.variant_id)
            if not variant or variant.product_id != data.product_id:
                raise HTTPException(status_code=400, detail="Variant does not belong to this product")
        row = get_warehouse_stock_row(db, warehouse_id, data.product_id, data.variant_id)
        current_quantity = row.quantity if row else 0
        usage = get_warehouse_usage(db, warehouse_id)
        projected_usage = usage - current_quantity + data.quantity
        if projected_usage > warehouse.capacity_units:
            raise HTTPException(status_code=409, detail="Warehouse capacity exceeded")
        if row:
            row.quantity = data.quantity
        else:
            row = WarehouseInventory(warehouse_id=warehouse_id, product_id=data.product_id, variant_id=data.variant_id, quantity=data.quantity)
            db.add(row)
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        raise

def list_warehouse_stock(db: Session, warehouse_id: int):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    return db.scalars(select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse.id).order_by(WarehouseInventory.product_id)).all()

def get_product_warehouse_stock(db: Session, product_id: int, variant_id: int | None = None):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id:
            raise HTTPException(status_code=400, detail="Variant does not belong to this product")
    statement = select(WarehouseInventory).join(Warehouse, Warehouse.id == WarehouseInventory.warehouse_id).where(WarehouseInventory.product_id == product_id, Warehouse.status == WarehouseStatus.ACTIVE)
    statement = statement.where(WarehouseInventory.variant_id == variant_id) if variant_id is not None else statement.where(WarehouseInventory.variant_id.is_(None))
    return db.scalars(statement.order_by(Warehouse.name)).all()
