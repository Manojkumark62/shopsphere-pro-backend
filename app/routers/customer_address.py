from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_roles
from app.models.auth import User
from app.schemas.customer_address import CustomerAddressCreate, CustomerAddressUpdate, CustomerAddressResponse
from app.services.customer_address_service import create_address, list_addresses, update_address, delete_address, set_default_address


router = APIRouter(prefix="/api/v1/addresses", tags=["Customer Addresses"])


@router.post("/", response_model=CustomerAddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(payload: CustomerAddressCreate, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    return create_address(db, current_user.id, payload.model_dump())


@router.get("/", response_model=list[CustomerAddressResponse])
def get_addresses(current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    return list_addresses(db, current_user.id)


@router.get("/{address_id}", response_model=CustomerAddressResponse)
def get_address(address_id: int, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    from app.services.customer_address_service import get_customer_address
    return get_customer_address(db, address_id, current_user.id)


@router.patch("/{address_id}", response_model=CustomerAddressResponse)
def edit_address(address_id: int, payload: CustomerAddressUpdate, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    return update_address(db, address_id, current_user.id, payload.model_dump(exclude_unset=True))


@router.delete("/{address_id}")
def remove_address(address_id: int, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    return delete_address(db, address_id, current_user.id)


@router.patch("/{address_id}/default/{address_type}", response_model=CustomerAddressResponse)
def make_default_address(address_id: int, address_type: str, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    return set_default_address(db, address_id, current_user.id, address_type.lower())