
import phonenumbers
from pydantic import BaseModel, EmailStr, Field, field_validator

class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone_number: str = Field(min_length=5, max_length=30)
    country_code: str = Field(default="IN", min_length=2, max_length=2)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value):
        value = " ".join(value.split())
        if not value or not any(char.isalpha() for char in value):
            raise ValueError("Enter a valid full name")
        return value

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value, info):
        country = info.data.get("country_code", "IN")
        try:
            number = phonenumbers.parse(value, country)
            if not phonenumbers.is_valid_number(number):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number")

class CustomerRegistrationResponse(BaseModel):
    message: str
    email: EmailStr
    verification_token: str

class EmailVerificationResponse(BaseModel):
    message: str

