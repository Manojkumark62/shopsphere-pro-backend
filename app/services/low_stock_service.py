from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.low_stock import StockThreshold, StockThresholdHistory, StockRestockAlert
from app.models.warehouse import Warehouse
from app.models.warehouse_inventory import WarehouseInventory
from app.models.product import Product
from app.models.product_variant import ProductVariant


def validate_stock_target(db: Session, warehouse_id: int, product_id: int, variant_id: int | None):
    if not db.get(Warehouse, warehouse_id):
        raise HTTPException(status_code=404, detail="Warehouse not found")
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id:
            raise HTTPException(status_code=400, detail="Variant does not belong to this product")


def get_current_quantity(db: Session, warehouse_id: int, product_id: int, variant_id: int | None):
    statement = select(WarehouseInventory).where(WarehouseInventory.warehouse_id == warehouse_id, WarehouseInventory.product_id == product_id, WarehouseInventory.variant_id == variant_id)
    stock = db.scalar(statement)
    return stock.quantity if stock else 0


def create_threshold(db: Session, data, current_user):
    try:
        validate_stock_target(db, data.warehouse_id, data.product_id, data.variant_id)
        existing = db.scalar(select(StockThreshold).where(StockThreshold.warehouse_id == data.warehouse_id, StockThreshold.product_id == data.product_id, StockThreshold.variant_id == data.variant_id))
        if existing:
            raise HTTPException(status_code=409, detail="A threshold already exists for this stock item")
        threshold = StockThreshold(warehouse_id=data.warehouse_id, product_id=data.product_id, variant_id=data.variant_id, minimum_quantity=data.minimum_quantity)
        db.add(threshold)
        db.flush()
        db.add(StockThresholdHistory(threshold_id=threshold.id, old_quantity=None, new_quantity=data.minimum_quantity, changed_by=current_user.id, reason=data.reason or "Initial threshold"))
        db.commit()
        db.refresh(threshold)
        return threshold
    except Exception:
        db.rollback()
        raise


def update_threshold(db: Session, threshold_id: int, data, current_user):
    try:
        threshold = db.scalar(select(StockThreshold).where(StockThreshold.id == threshold_id).with_for_update())
        if not threshold:
            raise HTTPException(status_code=404, detail="Stock threshold not found")
        old_quantity = threshold.minimum_quantity
        threshold.minimum_quantity = data.minimum_quantity
        db.add(StockThresholdHistory(threshold_id=threshold.id, old_quantity=old_quantity, new_quantity=data.minimum_quantity, changed_by=current_user.id, reason=data.reason))
        db.commit()
        db.refresh(threshold)
        return threshold
    except Exception:
        db.rollback()
        raise


def list_thresholds(db: Session, warehouse_id: int | None = None):
    statement = select(StockThreshold).where(StockThreshold.is_active.is_(True)).order_by(StockThreshold.id.desc())
    if warehouse_id is not None:
        statement = statement.where(StockThreshold.warehouse_id == warehouse_id)
    return db.scalars(statement).all()


def deactivate_threshold(db: Session, threshold_id: int):
    threshold = db.get(StockThreshold, threshold_id)
    if not threshold:
        raise HTTPException(status_code=404, detail="Stock threshold not found")
    threshold.is_active = False
    db.commit()
    return {"message": "Stock threshold deactivated"}


def get_low_stock_items(db: Session, warehouse_id: int | None = None):
    statement = select(StockThreshold).where(StockThreshold.is_active.is_(True))
    if warehouse_id is not None:
        statement = statement.where(StockThreshold.warehouse_id == warehouse_id)
    thresholds = db.scalars(statement).all()
    results = []
    for threshold in thresholds:
        current_quantity = get_current_quantity(db, threshold.warehouse_id, threshold.product_id, threshold.variant_id)
        if current_quantity <= threshold.minimum_quantity:
            results.append({"warehouse_id": threshold.warehouse_id, "product_id": threshold.product_id, "variant_id": threshold.variant_id, "current_quantity": current_quantity, "minimum_quantity": threshold.minimum_quantity, "shortage_quantity": max(threshold.minimum_quantity - current_quantity, 0)})
    return results


def generate_restock_alerts(db: Session, warehouse_id: int | None = None):
    try:
        low_stock_items = get_low_stock_items(db, warehouse_id)
        created_alerts = []
        for item in low_stock_items:
            threshold = db.scalar(select(StockThreshold).where(StockThreshold.warehouse_id == item["warehouse_id"], StockThreshold.product_id == item["product_id"], StockThreshold.variant_id == item["variant_id"], StockThreshold.is_active.is_(True)))
            if not threshold:
                continue
            existing_alert = db.scalar(select(StockRestockAlert).where(StockRestockAlert.threshold_id == threshold.id, StockRestockAlert.status == "open"))
            if existing_alert:
                existing_alert.current_quantity = item["current_quantity"]
                existing_alert.minimum_quantity = item["minimum_quantity"]
                continue
            alert = StockRestockAlert(threshold_id=threshold.id, warehouse_id=item["warehouse_id"], product_id=item["product_id"], variant_id=item["variant_id"], current_quantity=item["current_quantity"], minimum_quantity=item["minimum_quantity"], status="open")
            db.add(alert)
            created_alerts.append(alert)
        db.commit()
        for alert in created_alerts:
            db.refresh(alert)
        return created_alerts
    except Exception:
        db.rollback()
        raise


def list_restock_alerts(db: Session, status: str | None = None, warehouse_id: int | None = None):
    statement = select(StockRestockAlert).order_by(StockRestockAlert.created_at.desc())
    if status:
        statement = statement.where(StockRestockAlert.status == status)
    if warehouse_id is not None:
        statement = statement.where(StockRestockAlert.warehouse_id == warehouse_id)
    return db.scalars(statement).all()


def resolve_restock_alert(db: Session, alert_id: int):
    alert = db.get(StockRestockAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Restock alert not found")
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


def get_threshold_history(db: Session, threshold_id: int):
    if not db.get(StockThreshold, threshold_id):
        raise HTTPException(status_code=404, detail="Stock threshold not found")
    statement = select(StockThresholdHistory).where(StockThresholdHistory.threshold_id == threshold_id).order_by(StockThresholdHistory.created_at.desc())
    return db.scalars(statement).all()


def get_low_stock_report(db: Session, warehouse_id: int | None = None):
    items = get_low_stock_items(db, warehouse_id)
    return {"total_low_stock_items": len(items), "total_shortage_units": sum(item["shortage_quantity"] for item in items), "items": items}