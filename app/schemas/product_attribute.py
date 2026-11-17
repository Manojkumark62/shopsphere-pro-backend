
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal

class ProductAttributeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=100)
    data_type: Literal["text", "number", "boolean"] = "text"
    allowed_values: list[str] | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        value = value.strip().lower().replace(" ", "_")
        if not value.replace("_", "").isalnum():
            raise ValueError("Code must contain only letters, numbers, and underscores")
        return value

    @field_validator("allowed_values")
    @classmethod
    def validate_allowed_values(cls, values):
        if values is not None and (not values or any(not item.strip() for item in values)):
            raise ValueError("Allowed values cannot be empty")
        return values

class CategoryAttributeCreate(BaseModel):
    attribute_id: int = Field(gt=0)
    is_required: bool = False

class ProductAttributeValueCreate(BaseModel):
    attribute_id: int = Field(gt=0)
    value: str = Field(min_length=1, max_length=500)

class ProductAttributeResponse(BaseModel):
    id: int
    name: str
    code: str
    data_type: str
    allowed_values: list[str] | None
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ProductAttributeValueResponse(BaseModel):
    id: int
    product_id: int
    attribute_id: int
    value: str
    model_config = ConfigDict(from_attributes=True)
