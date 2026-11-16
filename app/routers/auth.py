
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.auth import LoginRequest, TokenRefreshRequest, LogoutRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, issue_tokens, refresh_user_tokens, revoke_user_tokens
from app.dependencies.auth import get_current_user, require_roles, oauth2_scheme
from app.models.auth import User, RefreshToken
from app.core.security import decode_token, hash_token



router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse)
def oauth2_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    return issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    return issue_tokens(db, user)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: TokenRefreshRequest, db: Session = Depends(get_db)):
    return refresh_user_tokens(db, data.refresh_token)

@router.post("/logout")
def logout(data: LogoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), access_token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid access token")
    stored = db.query(RefreshToken).filter_by(token_hash=hash_token(data.refresh_token), user_id=current_user.id, revoked=False).first()
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return revoke_user_tokens(db, data.refresh_token, payload)

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin-only")
def admin_only(current_user: User = Depends(require_roles("admin"))):
    return {"message": "Welcome Admin", "user": current_user.email}

@router.get("/employee-only")
def employee_only(current_user: User = Depends(require_roles("employee", "admin"))):
    return {"message": "Welcome Employee", "user": current_user.email}
