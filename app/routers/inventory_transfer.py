from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.models.inventory_transfer import TransferStatus
from app.schemas.inventory_transfer import (
    InventoryTransferCreate,
    InventoryTransferDispatch,
    InventoryTransferReceive,
    InventoryTransferResponse,
    TransferMovementResponse,
)
from app.services.inventory_transfer_service import (
    cancel_transfer,
    create_transfer,
    dispatch_transfer,
    get_transfer_history,
    list_transfers,
    receive_transfer,
)

router = APIRouter(
    prefix="/api/v1/inventory-transfers",
    tags=["Inventory Transfers"],
)


@router.post(
    "/",
    response_model=InventoryTransferResponse,
    status_code=201,
)
def create_transfer_request(
    data: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "employee")),
):
    return create_transfer(db, data, current_user)


@router.get(
    "/",
    response_model=list[InventoryTransferResponse],
)
def get_transfers(
    status: TransferStatus | None = Query(default=None),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "employee")),
):
    return list_transfers(db, status, warehouse_id)


@router.post(
    "/{transfer_id}/dispatch",
    response_model=InventoryTransferResponse,
)
def dispatch_inventory_transfer(
    transfer_id: int,
    data: InventoryTransferDispatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "employee")),
):
    return dispatch_transfer(db, transfer_id, data, current_user)


@router.post(
    "/{transfer_id}/receive",
    response_model=InventoryTransferResponse,
)
def receive_inventory_transfer(
    transfer_id: int,
    data: InventoryTransferReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "employee")),
):
    return receive_transfer(db, transfer_id, data, current_user)


@router.post(
    "/{transfer_id}/cancel",
    response_model=InventoryTransferResponse,
)
def cancel_inventory_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    return cancel_transfer(db, transfer_id, current_user)


@router.get(
    "/{transfer_id}/history",
    response_model=list[TransferMovementResponse],
)
def get_inventory_transfer_history(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "employee")),
):
    return get_transfer_history(db, transfer_id)