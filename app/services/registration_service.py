
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.auth import User, UserRole
from app.models.customer_registration import CustomerProfile, EmailVerification
from app.core.security import hash_password
from app.core.security import utc_naive


def issue_email_verification(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id,
        EmailVerification.is_used == False,
    ).update({"is_used": True})
    verification = EmailVerification(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=utc_naive(
            datetime.now(timezone.utc) + timedelta(minutes=30)
        ),
    )
    db.add(verification)
    return token


def register_customer(db: Session, data):
    email = str(data.email).strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.query(CustomerProfile).filter(CustomerProfile.phone_number == data.phone_number).first():
        raise HTTPException(status_code=409, detail="Phone number already registered")
    user = User(email=email, password_hash=hash_password(data.password), role=UserRole.CUSTOMER, is_active=True, is_verified=False)
    try:
        db.add(user)
        db.flush()
        profile = CustomerProfile(user_id=user.id, full_name=data.full_name, phone_number=data.phone_number)
        token = issue_email_verification(db, user)
        db.add(profile)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email or phone number already registered")
    return {
        "message": "Registration successful. Use the verification token to verify your email.",
        "email": email,
        "verification_token": token,
    }

def verify_customer_email(db: Session, token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    verification = db.query(EmailVerification).filter(EmailVerification.token_hash == token_hash, EmailVerification.is_used == False).with_for_update().first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not verification or verification.expires_at <= now:
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired")
    user = db.query(User).filter(User.id == verification.user_id).with_for_update().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Customer account is unavailable")
    verification.is_used = True
    user.is_verified = True
    db.query(EmailVerification).filter(EmailVerification.user_id == user.id, EmailVerification.id != verification.id, EmailVerification.is_used == False).update({"is_used": True})
    db.commit()
    return {"message": "Email verified successfully. Your account is now active."}
