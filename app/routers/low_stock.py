from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.low_stock import StockThresholdCreate, StockThresholdUpdate, StockThresholdResponse, LowStockItemResponse, StockThresholdHistoryResponse, RestockAlertResponse
from app.services.low_stock_service import create_threshold, update_threshold, list_thresholds, deactivate_threshold, get_low_stock_items, generate_restock_alerts, list_restock_alerts, resolve_restock_alert, get_threshold_history, get_low_stock_report

router = APIRouter(prefix="/api/v1/low-stock", tags=["Low Stock Management"])


@router.post("/thresholds", response_model=StockThresholdResponse, status_code=201)
def create_stock_threshold(data: StockThresholdCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return create_threshold(db, data, current_user)


@router.patch("/thresholds/{threshold_id}", response_model=StockThresholdResponse)
def update_stock_threshold(threshold_id: int, data: StockThresholdUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return update_threshold(db, threshold_id, data, current_user)


@router.get("/thresholds", response_model=list[StockThresholdResponse])
def get_stock_thresholds(warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return list_thresholds(db, warehouse_id)


@router.delete("/thresholds/{threshold_id}")
def delete_stock_threshold(threshold_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return deactivate_threshold(db, threshold_id)


@router.get("/items", response_model=list[LowStockItemResponse])
def get_low_stock(warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return get_low_stock_items(db, warehouse_id)


@router.post("/alerts/generate", response_model=list[RestockAlertResponse])
def generate_alerts(warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return generate_restock_alerts(db, warehouse_id)


@router.get("/alerts", response_model=list[RestockAlertResponse])
def get_restock_alerts(status: str | None = Query(default=None, pattern="^(open|resolved)$"), warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return list_restock_alerts(db, status, warehouse_id)


@router.patch("/alerts/{alert_id}/resolve", response_model=RestockAlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return resolve_restock_alert(db, alert_id)


@router.get("/thresholds/{threshold_id}/history", response_model=list[StockThresholdHistoryResponse])
def get_stock_threshold_history(threshold_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return get_threshold_history(db, threshold_id)


@router.get("/report")
def low_stock_report(warehouse_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin", "employee"))):
    return get_low_stock_report(db, warehouse_id)