from pydantic import BaseModel, Field, field_validator


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: int | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Category name cannot be empty")
        return value.strip()


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Category name cannot be empty")
        return value.strip() if value else value


class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    parent_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class ProductCategoryTreeResponse(ProductCategoryResponse):
    children: list["ProductCategoryTreeResponse"] = []