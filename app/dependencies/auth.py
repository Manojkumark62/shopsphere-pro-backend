
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.database.connection import get_db
from app.core.security import decode_token
from app.models.auth import User, UserRole, RevokedAccessToken
from app.services.auth_service import hash_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(status_code=401, detail="Invalid authentication credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(token)
        if payload.get("type") != "access" or not payload.get("sub") or not payload.get("jti"):
            raise credentials_error
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise credentials_error
    revoked = db.query(RevokedAccessToken).filter(RevokedAccessToken.jti == payload["jti"]).first()
    if revoked:
        raise credentials_error
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user or (user.role == UserRole.CUSTOMER and not user.is_verified):
        raise credentials_error
    return user

def require_roles(*roles):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to access this resource")
        return current_user
    return role_checker
