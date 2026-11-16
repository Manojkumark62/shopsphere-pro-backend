
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError
from app.models.auth import User, RefreshToken, RevokedAccessToken, UserRole
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token, hash_token, utc_naive

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if user.role == UserRole.CUSTOMER and not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")
    return user

def issue_tokens(db: Session, user: User):
    access_token, access_jti, access_expiry = create_access_token(user.id, user.role.value)
    refresh_token, refresh_expiry = create_refresh_token(user.id)
    db.add(RefreshToken(token_hash=hash_token(refresh_token), user_id=user.id, expires_at=utc_naive(refresh_expiry)))
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

def refresh_user_tokens(db: Session, token: str):
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(token), RefreshToken.revoked == False).with_for_update().first()
    if not stored_token or stored_token.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user or (user.role == UserRole.CUSTOMER and not user.is_verified):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    stored_token.revoked = True
    access_token, access_jti, access_expiry = create_access_token(user.id, user.role.value)
    refresh_token, refresh_expiry = create_refresh_token(user.id)
    db.add(RefreshToken(token_hash=hash_token(refresh_token), user_id=user.id, expires_at=utc_naive(refresh_expiry)))
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

def revoke_user_tokens(db: Session, refresh_token: str, access_payload: dict):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token), RefreshToken.revoked == False).with_for_update().first()
    if stored_token:
        stored_token.revoked = True
    jti = access_payload.get("jti")
    if jti:
        already_revoked = db.query(RevokedAccessToken).filter(RevokedAccessToken.jti == jti).first()
        if not already_revoked:
            expiry = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
            db.add(RevokedAccessToken(jti=jti, expires_at=utc_naive(expiry)))
    db.commit()
    return {"message": "Successfully logged out"}
