from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.auth import User
from app.schemas.customer_profile import CustomerProfileUpdate, CustomerProfileResponse, DeactivationRequestCreate, DeactivationReview
from app.services.customer_profile_service import get_customer_profile, profile_response, update_customer_profile, get_profile_history, create_deactivation_request, list_deactivation_requests, review_deactivation_request


router = APIRouter(prefix="/api/v1/profiles", tags=["Customer Profile"])


@router.get("/me", response_model=CustomerProfileResponse)
def get_my_profile(current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    user, profile = get_customer_profile(db, current_user.id)
    return profile_response(user, profile)


@router.patch("/me", response_model=CustomerProfileResponse, response_model_exclude_none=True)
def update_my_profile(payload: CustomerProfileUpdate, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True, exclude={"country_code"})
    return update_customer_profile(db, current_user.id, data)


@router.get("/{user_id}", response_model=CustomerProfileResponse)
def get_customer_profile_by_admin(user_id: int, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    user, profile = get_customer_profile(db, user_id)
    return profile_response(user, profile)


@router.get("/{user_id}/history")
def get_customer_profile_history(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You cannot access this profile history")
    return get_profile_history(db, user_id)


@router.post("/me/deactivation-request")
def request_account_deactivation(payload: DeactivationRequestCreate, current_user: User = Depends(require_roles("customer")), db: Session = Depends(get_db)):
    request = create_deactivation_request(db, current_user.id, payload.reason)
    return {"message": "Deactivation request submitted", "request_id": request.id, "status": request.status.value}


@router.get("/deactivation-requests")
def get_deactivation_requests(current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return list_deactivation_requests(db)


@router.patch("/deactivation-requests/{request_id}")
def review_deactivation(request_id: int, payload: DeactivationReview, current_user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    request = review_deactivation_request(db, request_id, current_user.id, payload.status.lower())
    return {"message": "Deactivation request reviewed", "request_id": request.id, "status": request.status.value}