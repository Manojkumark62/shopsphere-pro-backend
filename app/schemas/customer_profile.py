from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers


class CustomerProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    country_code: str = "IN"
    phone_number: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Name cannot be empty")
        return value.strip() if value else value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value, info):
        if value is None:
            return value
        country = info.data.get("country_code", "IN")
        try:
            parsed = phonenumbers.parse(value, country)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number")


class CustomerProfileResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    phone_number: str
    is_verified: bool
    is_active: bool
    verification_token: str | None = None


class DeactivationRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class DeactivationReview(BaseModel):
    status: str


class DeactivationRequestResponse(BaseModel):
    id: int
    user_id: int
    reason: str | None
    status: str
    requested_at: datetime


class ProfileHistoryResponse(BaseModel):
    id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime