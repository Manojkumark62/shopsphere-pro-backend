from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.auth import User, UserRole, RefreshToken
from app.models.customer_registration import CustomerProfile
from app.models.customer_profile_management import ProfileChangeHistory, AccountDeactivationRequest, DeactivationStatus
from app.services.registration_service import issue_email_verification


def get_customer_profile(db: Session, user_id: int):
    user = db.get(User, user_id)
    profile = db.scalar(select(CustomerProfile).where(CustomerProfile.user_id == user_id))
    if not user or not profile:
        raise HTTPException(status_code=404, detail="Customer profile not found")
    return user, profile


def profile_response(user: User, profile: CustomerProfile):
    return {"user_id": user.id, "full_name": profile.full_name, "email": user.email, "phone_number": profile.phone_number, "is_verified": user.is_verified, "is_active": user.is_active}


def update_customer_profile(db: Session, user_id: int, data: dict):
    user, profile = get_customer_profile(db, user_id)
    changes = []
    verification_token = None

    if "email" in data and data["email"] is not None:
        new_email = str(data["email"]).lower()
        existing = db.scalar(select(User).where(User.email == new_email, User.id != user_id))
        if existing:
            raise HTTPException(status_code=409, detail="Email is already registered")
        if new_email != user.email:
            changes.append(("email", user.email, new_email))
            user.email = new_email
            user.is_verified = False
            verification_token = issue_email_verification(db, user)
            active_tokens = db.scalars(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked == False,
                )
            ).all()
            for refresh_token in active_tokens:
                refresh_token.revoked = True

    if "full_name" in data and data["full_name"] is not None and data["full_name"] != profile.full_name:
        changes.append(("full_name", profile.full_name, data["full_name"]))
        profile.full_name = data["full_name"]

    if "phone_number" in data and data["phone_number"] is not None and data["phone_number"] != profile.phone_number:
        duplicate = db.scalar(select(CustomerProfile).where(CustomerProfile.phone_number == data["phone_number"], CustomerProfile.user_id != user_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Phone number is already registered")
        changes.append(("phone_number", profile.phone_number, data["phone_number"]))
        profile.phone_number = data["phone_number"]

    for field, old_value, new_value in changes:
        db.add(ProfileChangeHistory(user_id=user_id, changed_by_user_id=user_id, field_name=field, old_value=old_value, new_value=new_value))

    db.commit()
    db.refresh(user)
    db.refresh(profile)
    response = profile_response(user, profile)
    if verification_token:
        response["verification_token"] = verification_token
    return response


def get_profile_history(db: Session, user_id: int):
    return db.scalars(select(ProfileChangeHistory).where(ProfileChangeHistory.user_id == user_id).order_by(ProfileChangeHistory.changed_at.desc())).all()


def create_deactivation_request(db: Session, user_id: int, reason: str | None):
    existing = db.scalar(select(AccountDeactivationRequest).where(AccountDeactivationRequest.user_id == user_id, AccountDeactivationRequest.status == DeactivationStatus.PENDING))
    if existing:
        raise HTTPException(status_code=409, detail="A deactivation request is already pending")

    request = AccountDeactivationRequest(user_id=user_id, reason=reason)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def list_deactivation_requests(db: Session):
    return db.scalars(select(AccountDeactivationRequest).order_by(AccountDeactivationRequest.requested_at.desc())).all()


def review_deactivation_request(db: Session, request_id: int, admin_id: int, status: str):
    request = db.get(AccountDeactivationRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Deactivation request not found")
    if request.status != DeactivationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Request has already been reviewed")
    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=422, detail="Status must be approved or rejected")

    request.status = DeactivationStatus(status)
    request.reviewed_by = admin_id
    request.reviewed_at = datetime.now(timezone.utc)

    if status == "approved":
        user = db.get(User, request.user_id)
        user.is_active = False
        tokens = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked == False)).all()
        for token in tokens:
            token.revoked = True

    db.commit()
    db.refresh(request)
    return request