
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.auth import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE

    @field_validator("role")
    @classmethod
    def reject_customer_role(cls, value: UserRole) -> UserRole:
        if value == UserRole.CUSTOMER:
            raise ValueError("Create customer accounts through customer registration")
        return value

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRole | None = None

    @field_validator("role")
    @classmethod
    def reject_customer_role(cls, value: UserRole | None) -> UserRole | None:
        if value == UserRole.CUSTOMER:
            raise ValueError("Customer roles are managed through customer registration")
        return value

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserActivityResponse(BaseModel):
    id: int
    actor_id: int
    target_user_id: int
    action: str
    details: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
