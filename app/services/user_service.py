
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from app.models.auth import User, UserRole
from app.models.user_management import UserActivity
from app.core.security import hash_password

def log_activity(db: Session, actor_id: int, target_id: int, action: str, details: str):
    db.add(UserActivity(actor_id=actor_id, target_user_id=target_id, action=action, details=details))

def get_user_or_404(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def ensure_admin_can_be_changed(db: Session, user: User, new_role=None, new_status=None):
    removing_admin = user.role == UserRole.ADMIN and (new_role is not None and new_role != UserRole.ADMIN or new_status is False)
    if removing_admin and user.is_active:
        active_admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove or deactivate the last active administrator")

def create_user(db: Session, data, actor: User):
    if data.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=400, detail="Create customer accounts through customer registration")
    email = str(data.email).strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
        is_verified=True,
    )
    try:
        db.add(user)
        db.flush()
        log_activity(db, actor.id, user.id, "USER_CREATED", f"Created account with role {user.role.value}")
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")

def update_user(db: Session, user_id: int, data, actor: User):
    user = get_user_or_404(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No update fields provided")
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Update fields cannot be null")
    if user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=400,
            detail="Customer account details must be changed through customer profile management",
        )
    if changes.get("role") == UserRole.CUSTOMER:
        raise HTTPException(status_code=400, detail="Customer roles are managed through customer registration")
    old_role = user.role
    new_role = changes.get("role")
    if new_role is not None:
        ensure_admin_can_be_changed(db, user, new_role=new_role)
        user.role = new_role
    if "email" in changes:
        email = str(changes["email"]).strip().lower()
        if db.query(User).filter(User.email == email, User.id != user.id).first():
            raise HTTPException(status_code=409, detail="Email already registered")
        user.email = email
    details = f"Updated fields: {', '.join(changes.keys())}"
    if old_role != user.role:
        details += f"; role changed from {old_role.value} to {user.role.value}"
    log_activity(db, actor.id, user.id, "USER_UPDATED", details)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")

def update_user_status(db: Session, user_id: int, is_active: bool, actor: User):
    user = get_user_or_404(db, user_id)
    if user.id == actor.id and not is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    ensure_admin_can_be_changed(db, user, new_status=is_active)
    if user.is_active == is_active:
        return user
    user.is_active = is_active
    action = "USER_ACTIVATED" if is_active else "USER_DEACTIVATED"
    log_activity(db, actor.id, user.id, action, f"Account active status changed to {is_active}")
    db.commit()
    db.refresh(user)
    return user

def search_users(db: Session, search=None, role=None, is_active=None, skip=0, limit=20):
    query = db.query(User)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(User.email.ilike(term))
    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.order_by(User.id.desc()).offset(skip).limit(limit).all()

def get_user_activities(db: Session, user_id: int, skip=0, limit=20):
    get_user_or_404(db, user_id)
    return db.query(UserActivity).filter(UserActivity.target_user_id == user_id).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
