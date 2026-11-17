from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inventory_transfer import (
    InventoryTransfer,
    InventoryTransferMovement,
    TransferMovementType,
    TransferStatus,
)
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseStatus
from app.models.warehouse_inventory import WarehouseInventory


def get_transfer_or_404(db: Session, transfer_id: int):
    transfer = db.get(InventoryTransfer, transfer_id)

    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    return transfer


def get_active_warehouse_or_404(db: Session, warehouse_id: int):
    warehouse = db.scalar(
        select(Warehouse)
        .where(Warehouse.id == warehouse_id)
        .with_for_update()
    )

    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    if warehouse.status != WarehouseStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Warehouse is not active",
        )

    return warehouse


def validate_product_and_variant(
    db: Session,
    product_id: int,
    variant_id: int | None,
):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)

        if not variant or variant.product_id != product_id:
            raise HTTPException(
                status_code=400,
                detail="Variant does not belong to this product",
            )


def get_stock_row(
    db: Session,
    warehouse_id: int,
    product_id: int,
    variant_id: int | None,
):
    statement = (
        select(WarehouseInventory)
        .where(
            WarehouseInventory.warehouse_id == warehouse_id,
            WarehouseInventory.product_id == product_id,
            WarehouseInventory.variant_id == variant_id,
        )
        .with_for_update()
    )

    return db.scalar(statement)


def require_source_stock(
    source_stock: WarehouseInventory | None,
    warehouse_id: int,
    product_id: int,
    variant_id: int | None,
    required_quantity: int,
):
    available_quantity = source_stock.quantity if source_stock else 0
    if available_quantity < required_quantity:
        available_unit = "unit" if available_quantity == 1 else "units"
        required_unit = "unit" if required_quantity == 1 else "units"
        item_variant = (
            f"variant {variant_id}" if variant_id is not None else "base product"
        )
        raise HTTPException(
            status_code=409,
            detail=(
                f"Insufficient source warehouse stock: warehouse {warehouse_id} "
                f"has {available_quantity} {available_unit} for product {product_id} "
                f"({item_variant}); {required_quantity} {required_unit} required. "
                "Set the warehouse stock before creating or dispatching the transfer."
            ),
        )


def add_movement(
    db: Session,
    transfer: InventoryTransfer,
    movement_type: TransferMovementType,
    quantity: int,
    performed_by: int,
    from_warehouse_id: int | None = None,
    to_warehouse_id: int | None = None,
    note: str | None = None,
):
    movement = InventoryTransferMovement(
        transfer_id=transfer.id,
        movement_type=movement_type,
        quantity=quantity,
        performed_by=performed_by,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        note=note,
    )
    db.add(movement)


def create_transfer(db: Session, data, current_user):
    try:
        if data.source_warehouse_id == data.destination_warehouse_id:
            raise HTTPException(
                status_code=400,
                detail="Source and destination warehouses must differ",
            )

        get_active_warehouse_or_404(db, data.source_warehouse_id)
        get_active_warehouse_or_404(db, data.destination_warehouse_id)

        validate_product_and_variant(
            db,
            data.product_id,
            data.variant_id,
        )

        source_stock = get_stock_row(
            db,
            data.source_warehouse_id,
            data.product_id,
            data.variant_id,
        )
        require_source_stock(
            source_stock,
            data.source_warehouse_id,
            data.product_id,
            data.variant_id,
            data.requested_quantity,
        )

        transfer = InventoryTransfer(
            source_warehouse_id=data.source_warehouse_id,
            destination_warehouse_id=data.destination_warehouse_id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            requested_quantity=data.requested_quantity,
            note=data.note,
            requested_by=current_user.id,
            status=TransferStatus.PENDING,
        )

        db.add(transfer)
        db.flush()

        add_movement(
            db=db,
            transfer=transfer,
            movement_type=TransferMovementType.REQUESTED,
            quantity=data.requested_quantity,
            performed_by=current_user.id,
            from_warehouse_id=data.source_warehouse_id,
            to_warehouse_id=data.destination_warehouse_id,
            note=data.note,
        )

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def dispatch_transfer(db: Session, transfer_id: int, data, current_user):
    try:
        transfer = db.scalar(
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id)
            .with_for_update()
        )

        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")

        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Only pending transfers can be dispatched",
            )

        if data.quantity > transfer.requested_quantity:
            raise HTTPException(
                status_code=400,
                detail="Dispatch quantity exceeds requested quantity",
            )

        get_active_warehouse_or_404(db, transfer.source_warehouse_id)

        source_stock = get_stock_row(
            db,
            transfer.source_warehouse_id,
            transfer.product_id,
            transfer.variant_id,
        )
        require_source_stock(
            source_stock,
            transfer.source_warehouse_id,
            transfer.product_id,
            transfer.variant_id,
            data.quantity,
        )

        source_stock.quantity -= data.quantity
        source_stock.updated_at = datetime.utcnow()

        transfer.dispatched_quantity = data.quantity
        transfer.dispatched_by = current_user.id
        transfer.dispatched_at = datetime.utcnow()
        transfer.status = TransferStatus.DISPATCHED

        add_movement(
            db=db,
            transfer=transfer,
            movement_type=TransferMovementType.DISPATCHED,
            quantity=data.quantity,
            performed_by=current_user.id,
            from_warehouse_id=transfer.source_warehouse_id,
            to_warehouse_id=transfer.destination_warehouse_id,
            note=data.note,
        )

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def receive_transfer(db: Session, transfer_id: int, data, current_user):
    try:
        transfer = db.scalar(
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id)
            .with_for_update()
        )

        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")

        if transfer.status not in (
            TransferStatus.DISPATCHED,
            TransferStatus.PARTIALLY_RECEIVED,
        ):
            raise HTTPException(
                status_code=400,
                detail="This transfer cannot receive stock",
            )

        remaining = transfer.dispatched_quantity - transfer.received_quantity

        if data.quantity > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"Only {remaining} units remain to be received",
            )

        destination = get_active_warehouse_or_404(
            db,
            transfer.destination_warehouse_id,
        )

        # Lock the destination warehouse while checking capacity.
        current_usage = db.scalar(
            select(func.coalesce(func.sum(WarehouseInventory.quantity), 0))
            .where(WarehouseInventory.warehouse_id == destination.id)
        ) or 0

        destination_stock = get_stock_row(
            db,
            destination.id,
            transfer.product_id,
            transfer.variant_id,
        )

        existing_quantity = destination_stock.quantity if destination_stock else 0
        additional_capacity = data.quantity

        if (
            destination.capacity_units is not None
            and current_usage + additional_capacity > destination.capacity_units
        ):
            raise HTTPException(
                status_code=400,
                detail="Destination warehouse capacity would be exceeded",
            )

        if destination_stock:
            destination_stock.quantity += data.quantity
            destination_stock.updated_at = datetime.utcnow()
        else:
            destination_stock = WarehouseInventory(
                warehouse_id=destination.id,
                product_id=transfer.product_id,
                variant_id=transfer.variant_id,
                quantity=data.quantity,
            )
            db.add(destination_stock)

        transfer.received_quantity += data.quantity
        transfer.received_by = current_user.id

        if transfer.received_quantity == transfer.dispatched_quantity:
            transfer.status = TransferStatus.RECEIVED
            transfer.received_at = datetime.utcnow()
        else:
            transfer.status = TransferStatus.PARTIALLY_RECEIVED

        add_movement(
            db=db,
            transfer=transfer,
            movement_type=TransferMovementType.RECEIVED,
            quantity=data.quantity,
            performed_by=current_user.id,
            from_warehouse_id=transfer.source_warehouse_id,
            to_warehouse_id=transfer.destination_warehouse_id,
            note=data.note,
        )

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def cancel_transfer(db: Session, transfer_id: int, current_user):
    try:
        transfer = db.scalar(
            select(InventoryTransfer)
            .where(InventoryTransfer.id == transfer_id)
            .with_for_update()
        )

        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")

        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Only pending transfers can be cancelled",
            )

        transfer.status = TransferStatus.CANCELLED

        add_movement(
            db=db,
            transfer=transfer,
            movement_type=TransferMovementType.CANCELLED,
            quantity=0,
            performed_by=current_user.id,
            from_warehouse_id=transfer.source_warehouse_id,
            to_warehouse_id=transfer.destination_warehouse_id,
        )

        db.commit()
        db.refresh(transfer)
        return transfer

    except Exception:
        db.rollback()
        raise


def list_transfers(
    db: Session,
    status: TransferStatus | None = None,
    warehouse_id: int | None = None,
):
    statement = select(InventoryTransfer).order_by(
        InventoryTransfer.created_at.desc()
    )

    if status is not None:
        statement = statement.where(InventoryTransfer.status == status)

    if warehouse_id is not None:
        statement = statement.where(
            (
                InventoryTransfer.source_warehouse_id == warehouse_id
            ) | (
                InventoryTransfer.destination_warehouse_id == warehouse_id
            )
        )

    return db.scalars(statement).all()


def get_transfer_history(db: Session, transfer_id: int):
    get_transfer_or_404(db, transfer_id)

    statement = (
        select(InventoryTransferMovement)
        .where(InventoryTransferMovement.transfer_id == transfer_id)
        .order_by(InventoryTransferMovement.created_at.asc())
    )

    return db.scalars(statement).all()