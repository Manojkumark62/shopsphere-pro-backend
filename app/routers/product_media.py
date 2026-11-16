
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.auth import User
from app.schemas.product_media import ProductMediaResponse, ProductMediaUpdate
from app.services.product_media_service import upload_product_media, list_product_media, get_product_media, update_product_media, delete_product_media, get_media_path, MAX_UPLOAD_BYTES

router = APIRouter(prefix="/api/v1", tags=["Product Media"])

def format_media(media):
    return {"id": media.id, "product_id": media.product_id, "variant_id": media.variant_id, "media_type": media.media_type.value, "file_name": media.file_name, "content_type": media.content_type, "size_bytes": media.size_bytes, "alt_text": media.alt_text, "sort_order": media.sort_order, "is_primary": media.is_primary, "file_url": f"/api/v1/media/{media.id}/file", "created_at": media.created_at}

@router.post("/products/{product_id}/media", response_model=ProductMediaResponse)
async def upload_media(product_id: int, file: UploadFile = File(...), media_type: str | None = Form(None), variant_id: int | None = Form(None), alt_text: str | None = Form(None), sort_order: int = Form(0), is_primary: bool = Form(False), db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    media = upload_product_media(db, product_id, content, file.filename or "upload", file.content_type or "", media_type, variant_id, alt_text, sort_order, is_primary)
    return format_media(media)

@router.get("/products/{product_id}/media", response_model=list[ProductMediaResponse])
def get_product_media_list(product_id: int, db: Session = Depends(get_db)):
    return [format_media(media) for media in list_product_media(db, product_id)]

@router.get("/media/{media_id}", response_model=ProductMediaResponse)
def get_media_details(media_id: int, db: Session = Depends(get_db)):
    return format_media(get_product_media(db, media_id))

@router.get("/media/{media_id}/file")
def download_media(media_id: int, db: Session = Depends(get_db)):
    media = get_product_media(db, media_id)
    path = get_media_path(media.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.file_name,
        headers={"X-Content-Type-Options": "nosniff"},
    )

@router.patch("/media/{media_id}", response_model=ProductMediaResponse)
def edit_media(media_id: int, data: ProductMediaUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return format_media(update_product_media(db, media_id, data))

@router.delete("/media/{media_id}")
def remove_media(media_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("admin"))):
    return delete_product_media(db, media_id)
