
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ProductMediaUpdate(BaseModel):
    alt_text: str | None = Field(default=None, max_length=500)
    sort_order: int | None = Field(default=None, ge=0)
    is_primary: bool | None = None

class ProductMediaResponse(BaseModel):
    id: int
    product_id: int
    variant_id: int | None
    media_type: str
    file_name: str
    content_type: str
    size_bytes: int
    alt_text: str | None
    sort_order: int
    is_primary: bool
    file_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
