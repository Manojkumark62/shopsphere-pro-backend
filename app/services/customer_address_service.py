from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.customer_address import CustomerAddress


def get_customer_address(db: Session, address_id: int, user_id: int):
    address = db.scalar(select(CustomerAddress).where(CustomerAddress.id == address_id, CustomerAddress.user_id == user_id))
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


def clear_default_addresses(db: Session, user_id: int, billing: bool = False, shipping: bool = False):
    addresses = db.scalars(select(CustomerAddress).where(CustomerAddress.user_id == user_id)).all()
    for address in addresses:
        if billing:
            address.is_default_billing = False
        if shipping:
            address.is_default_shipping = False


def create_address(db: Session, user_id: int, data: dict):
    if data.get("is_default_billing") or data.get("is_default_shipping"):
        clear_default_addresses(db, user_id, data.get("is_default_billing", False), data.get("is_default_shipping", False))

    data.pop("country_code", None)
    address = CustomerAddress(user_id=user_id, **data)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, address_id: int, user_id: int, data: dict):
    address = get_customer_address(db, address_id, user_id)

    if data.get("is_default_billing") is True:
        clear_default_addresses(db, user_id, billing=True)
    if data.get("is_default_shipping") is True:
        clear_default_addresses(db, user_id, shipping=True)

    data.pop("country_code", None)
    for key, value in data.items():
        if value is not None:
            setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address


def list_addresses(db: Session, user_id: int):
    return db.scalars(select(CustomerAddress).where(CustomerAddress.user_id == user_id).order_by(CustomerAddress.created_at.desc())).all()


def delete_address(db: Session, address_id: int, user_id: int):
    address = get_customer_address(db, address_id, user_id)
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}


def set_default_address(db: Session, address_id: int, user_id: int, address_type: str):
    address = get_customer_address(db, address_id, user_id)

    if address_type == "billing":
        clear_default_addresses(db, user_id, billing=True)
        address.is_default_billing = True
    elif address_type == "shipping":
        clear_default_addresses(db, user_id, shipping=True)
        address.is_default_shipping = True
    else:
        raise HTTPException(status_code=422, detail="Address type must be billing or shipping")

    db.commit()
    db.refresh(address)
    return address