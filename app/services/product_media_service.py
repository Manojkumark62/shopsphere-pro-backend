
from pathlib import Path
import mimetypes
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.models.product import Product, ProductStatus
from app.models.product_variant import ProductVariant
from app.models.product_media import ProductMedia, MediaType

MEDIA_ROOT = Path("media").resolve()
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def get_product_or_404(db: Session, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def get_media_or_404(db: Session, media_id: int):
    media = db.get(ProductMedia, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Product media not found")
    return media

def get_media_path(storage_key: str):
    path = (MEDIA_ROOT / storage_key).resolve()
    if not path.is_relative_to(MEDIA_ROOT):
        raise HTTPException(status_code=400, detail="Invalid media storage path")
    return path

def upload_product_media(db: Session, product_id: int, content: bytes, filename: str, content_type: str, media_type: str | None, variant_id: int | None, alt_text: str | None, sort_order: int, is_primary: bool):
    product = get_product_or_404(db, product_id)
    if product.status in [ProductStatus.INACTIVE, ProductStatus.ARCHIVED]:
        raise HTTPException(status_code=400, detail="Cannot upload media to an inactive product")
    safe_filename = Path(filename).name
    content_type = content_type.partition(";")[0].strip().lower()
    if not content_type or len(content_type) > 100 or "/" not in content_type:
        content_type = mimetypes.guess_type(safe_filename)[0] or "application/octet-stream"
    media_type = "image" if content_type.startswith("image/") else "document"
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File must be between 1 byte and 10 MB")
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product_id:
            raise HTTPException(status_code=400, detail="Variant does not belong to this product")
    if is_primary and media_type != "image":
        raise HTTPException(status_code=400, detail="Only images can be primary")
    extension = Path(safe_filename).suffix.lower()
    stored_name = f"{uuid4().hex}{extension}"
    relative_key = f"products/{product_id}/{stored_name}"
    destination = get_media_path(relative_key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    try:
        if is_primary:
            db.query(ProductMedia).filter(ProductMedia.product_id == product_id, ProductMedia.is_primary.is_(True)).update({"is_primary": False})
        media = ProductMedia(product_id=product_id, variant_id=variant_id, media_type=MediaType(media_type), file_name=safe_filename[:255], storage_key=relative_key, content_type=content_type, size_bytes=len(content), alt_text=alt_text, sort_order=sort_order, is_primary=is_primary)
        db.add(media)
        db.commit()
        db.refresh(media)
        return media
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

def list_product_media(db: Session, product_id: int, public_only: bool = True):
    product = get_product_or_404(db, product_id)
    if public_only and product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Product not found")
    return db.scalars(select(ProductMedia).where(ProductMedia.product_id == product_id).order_by(ProductMedia.sort_order, ProductMedia.id)).all()

def get_product_media(db: Session, media_id: int, public_only: bool = True):
    media = get_media_or_404(db, media_id)
    product = get_product_or_404(db, media.product_id)
    if public_only and product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Media not found")
    return media

def update_product_media(db: Session, media_id: int, data):
    media = get_media_or_404(db, media_id)
    updates = data.model_dump(exclude_unset=True)
    if updates.get("is_primary") and media.media_type != MediaType.IMAGE:
        raise HTTPException(status_code=400, detail="Only images can be primary")
    if updates.get("is_primary"):
        db.query(ProductMedia).filter(ProductMedia.product_id == media.product_id, ProductMedia.id != media_id, ProductMedia.is_primary.is_(True)).update({"is_primary": False})
    for key, value in updates.items():
        setattr(media, key, value)
    db.commit()
    db.refresh(media)
    return media

def delete_product_media(db: Session, media_id: int):
    media = get_media_or_404(db, media_id)
    path = get_media_path(media.storage_key)
    db.delete(media)
    db.commit()
    path.unlink(missing_ok=True)
    return {"message": "Product media deleted successfully"}
