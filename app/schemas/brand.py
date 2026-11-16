from pydantic import BaseModel, Field, HttpUrl, field_validator


class BrandCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: HttpUrl | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Brand name cannot be empty")
        return value.strip()


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    logo_url: HttpUrl | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Brand name cannot be empty")
        return value.strip() if value else value


class BrandResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}