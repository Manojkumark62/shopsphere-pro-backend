from pydantic import BaseModel, Field, field_validator
from typing import Literal
import phonenumbers


class CustomerAddressCreate(BaseModel):
    address_type: Literal["home", "work", "other"] = "home"
    full_name: str = Field(min_length=2, max_length=150)
    phone_number: str = Field(min_length=7, max_length=20)
    address_line1: str = Field(min_length=3, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=3, max_length=20)
    country: str = Field(min_length=2, max_length=100)
    country_code: str = "IN"
    is_default_billing: bool = False
    is_default_shipping: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value, info):
        country = info.data.get("country_code", "IN")
        try:
            parsed = phonenumbers.parse(value, country)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number")

    @field_validator("full_name", "address_line1", "city", "state", "postal_code", "country")
    @classmethod
    def validate_text(cls, value):
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value.strip()


class CustomerAddressUpdate(BaseModel):
    address_type: Literal["home", "work", "other"] | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, min_length=7, max_length=20)
    address_line1: str | None = Field(default=None, min_length=3, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=3, max_length=20)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    country_code: str = "IN"
    is_default_billing: bool | None = None
    is_default_shipping: bool | None = None


class CustomerAddressResponse(BaseModel):
    id: int
    user_id: int
    address_type: str
    full_name: str
    phone_number: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    is_default_billing: bool
    is_default_shipping: bool

    model_config = {"from_attributes": True}