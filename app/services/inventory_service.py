
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.inventory import Inventory, InventoryMovement, InventoryMovementType
from app.models.product import Product
from app.models.product_variant import ProductVariant

def validate_product_variant(db: Session, product_id: int, variant_id: int | None):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id:
            raise HTTPException(status_code=400, detail="Variant does not belong to this product")
    return product

def get_inventory_locked(db: Session, product_id: int, variant_id: int | None):
    statement = select(Inventory).where(Inventory.product_id == product_id)
    statement = statement.where(Inventory.variant_id == variant_id) if variant_id is not None else statement.where(Inventory.variant_id.is_(None))
    return db.scalar(statement.with_for_update())

def get_or_create_inventory(db: Session, product_id: int, variant_id: int | None):
    validate_product_variant(db, product_id, variant_id)
    inventory = get_inventory_locked(db, product_id, variant_id)
    if inventory:
        return inventory
    inventory = Inventory(product_id=product_id, variant_id=variant_id, quantity_on_hand=0, reserved_quantity=0)
    db.add(inventory)
    db.flush()
    return inventory

def inventory_response(inventory: Inventory):
    return {"id": inventory.id, "product_id": inventory.product_id, "variant_id": inventory.variant_id, "quantity_on_hand": inventory.quantity_on_hand, "reserved_quantity": inventory.reserved_quantity, "available_quantity": inventory.quantity_on_hand - inventory.reserved_quantity, "updated_at": inventory.updated_at}

def record_movement(db: Session, inventory: Inventory, movement_type: InventoryMovementType, quantity: int, before: int, after: int, reserved_before: int, reserved_after: int, reason: str | None, user_id: int):
    db.add(InventoryMovement(inventory_id=inventory.id, movement_type=movement_type, quantity=quantity, quantity_before=before, quantity_after=after, reserved_before=reserved_before, reserved_after=reserved_after, reason=reason, performed_by=user_id))

def add_stock(db: Session, product_id: int, variant_id: int | None, quantity: int, reason: str, user_id: int):
    try:
        inventory = get_or_create_inventory(db, product_id, variant_id)
        before = inventory.quantity_on_hand
        reserved_before = inventory.reserved_quantity
        inventory.quantity_on_hand += quantity
        record_movement(db, inventory, InventoryMovementType.STOCK_IN, quantity, before, inventory.quantity_on_hand, reserved_before, inventory.reserved_quantity, reason, user_id)
        db.commit()
        db.refresh(inventory)
        return inventory_response(inventory)
    except Exception:
        db.rollback()
        raise

def reduce_stock(db: Session, product_id: int, variant_id: int | None, quantity: int, reason: str, user_id: int):
    try:
        inventory = get_or_create_inventory(db, product_id, variant_id)
        available = inventory.quantity_on_hand - inventory.reserved_quantity
        if quantity > available:
            raise HTTPException(status_code=409, detail="Insufficient available stock")
        before = inventory.quantity_on_hand
        reserved_before = inventory.reserved_quantity
        inventory.quantity_on_hand -= quantity
        record_movement(db, inventory, InventoryMovementType.STOCK_OUT, quantity, before, inventory.quantity_on_hand, reserved_before, inventory.reserved_quantity, reason, user_id)
        db.commit()
        db.refresh(inventory)
        return inventory_response(inventory)
    except Exception:
        db.rollback()
        raise

def reserve_stock(db: Session, product_id: int, variant_id: int | None, quantity: int, reason: str | None, user_id: int):
    try:
        inventory = get_or_create_inventory(db, product_id, variant_id)
        available = inventory.quantity_on_hand - inventory.reserved_quantity
        if quantity > available:
            raise HTTPException(status_code=409, detail="Insufficient available stock to reserve")
        before = inventory.quantity_on_hand
        reserved_before = inventory.reserved_quantity
        inventory.reserved_quantity += quantity
        record_movement(db, inventory, InventoryMovementType.RESERVE, quantity, before, before, reserved_before, inventory.reserved_quantity, reason, user_id)
        db.commit()
        db.refresh(inventory)
        return inventory_response(inventory)
    except Exception:
        db.rollback()
        raise

def release_stock(db: Session, product_id: int, variant_id: int | None, quantity: int, reason: str | None, user_id: int):
    try:
        inventory = get_or_create_inventory(db, product_id, variant_id)
        if quantity > inventory.reserved_quantity:
            quantity_unit = "unit" if quantity == 1 else "units"
            reserved_unit = "unit" if inventory.reserved_quantity == 1 else "units"
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot release {quantity} {quantity_unit} for product "
                    f"{product_id} (variant {variant_id}); only "
                    f"{inventory.reserved_quantity} {reserved_unit} are reserved."
                ),
            )
        before = inventory.quantity_on_hand
        reserved_before = inventory.reserved_quantity
        inventory.reserved_quantity -= quantity
        record_movement(db, inventory, InventoryMovementType.RELEASE, quantity, before, before, reserved_before, inventory.reserved_quantity, reason, user_id)
        db.commit()
        db.refresh(inventory)
        return inventory_response(inventory)
    except Exception:
        db.rollback()
        raise

def fulfill_reserved_stock(db: Session, product_id: int, variant_id: int | None, quantity: int, reason: str | None, user_id: int):
    try:
        inventory = get_or_create_inventory(db, product_id, variant_id)
        if quantity > inventory.reserved_quantity:
            quantity_unit = "unit" if quantity == 1 else "units"
            reserved_unit = "unit" if inventory.reserved_quantity == 1 else "units"
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot fulfill {quantity} {quantity_unit} for product "
                    f"{product_id} (variant {variant_id}); only "
                    f"{inventory.reserved_quantity} {reserved_unit} are reserved. "
                    "Reserve the quantity before fulfilling."
                ),
            )
        before = inventory.quantity_on_hand
        reserved_before = inventory.reserved_quantity
        inventory.quantity_on_hand -= quantity
        inventory.reserved_quantity -= quantity
        record_movement(db, inventory, InventoryMovementType.FULFILL, quantity, before, inventory.quantity_on_hand, reserved_before, inventory.reserved_quantity, reason, user_id)
        db.commit()
        db.refresh(inventory)
        return inventory_response(inventory)
    except Exception:
        db.rollback()
        raise

def get_inventory(db: Session, product_id: int, variant_id: int | None):
    validate_product_variant(db, product_id, variant_id)
    inventory = get_inventory_locked(db, product_id, variant_id)
    if not inventory:
        return {"product_id": product_id, "variant_id": variant_id, "quantity_on_hand": 0, "reserved_quantity": 0, "available_quantity": 0, "updated_at": None}
    return inventory_response(inventory)

def get_inventory_movements(db: Session, product_id: int, variant_id: int | None):
    validate_product_variant(db, product_id, variant_id)
    statement = select(InventoryMovement).join(Inventory, Inventory.id == InventoryMovement.inventory_id).where(Inventory.product_id == product_id)
    statement = statement.where(Inventory.variant_id == variant_id) if variant_id is not None else statement.where(Inventory.variant_id.is_(None))
    return db.scalars(statement.order_by(InventoryMovement.created_at.desc())).all()
