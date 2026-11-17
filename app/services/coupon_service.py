from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.coupon import Coupon, CouponUsage

CENT = Decimal("0.01")

def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

def normalize_coupon_code(code: str) -> str:
    return code.strip().upper()

def get_coupon_or_404(db: Session, coupon_id: int) -> Coupon:
    coupon = db.scalar(select(Coupon).where(Coupon.id == coupon_id))
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon

def create_coupon(db: Session, data, admin_id: int):
    code = normalize_coupon_code(data.code)
    if db.scalar(select(Coupon).where(Coupon.code == code)):
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    coupon = Coupon(**data.model_dump(exclude={"code"}), code=code, created_by=admin_id)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def list_coupons(db: Session, active_only: bool = False):
    query = select(Coupon).order_by(Coupon.created_at.desc())
    if active_only:
        query = query.where(Coupon.is_active.is_(True))
    return db.scalars(query).all()

def update_coupon(db: Session, coupon_id: int, data):
    coupon = get_coupon_or_404(db, coupon_id)
    updates = data.model_dump(exclude_unset=True)
    if "code" in updates:
        updates["code"] = normalize_coupon_code(updates["code"])
        existing = db.scalar(select(Coupon).where(Coupon.code == updates["code"], Coupon.id != coupon_id))
        if existing:
            raise HTTPException(status_code=409, detail="Coupon code already exists")
    for key, value in updates.items():
        setattr(coupon, key, value)
    effective_type = updates.get("discount_type", coupon.discount_type)
    effective_value = updates.get("discount_value", coupon.discount_value)
    effective_from = updates.get("valid_from", coupon.valid_from)
    effective_until = updates.get("valid_until", coupon.valid_until)
    effective_max = updates.get("max_discount", coupon.max_discount)
    if effective_until <= effective_from:
        raise HTTPException(status_code=400, detail="valid_until must be later than valid_from")
    if effective_type == "percentage" and effective_value > 100:
        raise HTTPException(status_code=400, detail="Percentage discount cannot exceed 100")
    if effective_type == "fixed" and effective_max is not None:
        raise HTTPException(status_code=400, detail="max_discount is only supported for percentage coupons")
    db.commit()
    db.refresh(coupon)
    return coupon

def set_coupon_active(db: Session, coupon_id: int, is_active: bool):
    coupon = get_coupon_or_404(db, coupon_id)
    coupon.is_active = is_active
    db.commit()
    db.refresh(coupon)
    return coupon

def validate_coupon(db: Session, coupon_code: str, customer_id: int, subtotal: Decimal):
    code = normalize_coupon_code(coupon_code)
    coupon = db.scalar(select(Coupon).where(Coupon.code == code))
    if not coupon or not coupon.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive coupon")
    now = datetime.utcnow()
    if now < coupon.valid_from or now >= coupon.valid_until:
        raise HTTPException(status_code=400, detail="Coupon is outside its validity period")
    subtotal = money(subtotal)
    if subtotal < coupon.min_purchase:
        raise HTTPException(status_code=400, detail=f"Minimum purchase required: {coupon.min_purchase}")
    total_uses = db.scalar(select(func.count(CouponUsage.id)).where(CouponUsage.coupon_id == coupon.id)) or 0
    if coupon.usage_limit is not None and total_uses >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit has been reached")
    customer_uses = db.scalar(select(func.count(CouponUsage.id)).where(CouponUsage.coupon_id == coupon.id, CouponUsage.customer_id == customer_id)) or 0
    if coupon.per_customer_limit is not None and customer_uses >= coupon.per_customer_limit:
        raise HTTPException(status_code=400, detail="You have reached this coupon's usage limit")
    if coupon.discount_type == "percentage":
        discount = money(subtotal * coupon.discount_value / Decimal("100"))
        if coupon.max_discount is not None:
            discount = min(discount, money(coupon.max_discount))
    else:
        discount = money(coupon.discount_value)
    return min(discount, subtotal)

def calculate_coupon_discount(db: Session, customer_id: int, coupon_code: str, subtotal: Decimal):
    return validate_coupon(db, coupon_code, customer_id, subtotal)

def record_coupon_redemption(db: Session, coupon_id: int, customer_id: int, order_reference: str | None = None):
    coupon = db.scalar(select(Coupon).where(Coupon.id == coupon_id).with_for_update())
    if not coupon or not coupon.is_active:
        raise HTTPException(status_code=400, detail="Coupon is not available")
    if order_reference and db.scalar(select(CouponUsage.id).where(CouponUsage.coupon_id == coupon_id, CouponUsage.order_reference == order_reference)):
        return None
    now = datetime.utcnow()
    if now < coupon.valid_from or now >= coupon.valid_until:
        raise HTTPException(status_code=400, detail="Coupon is outside its validity period")
    total_uses = db.scalar(select(func.count(CouponUsage.id)).where(CouponUsage.coupon_id == coupon_id)) or 0
    customer_uses = db.scalar(select(func.count(CouponUsage.id)).where(CouponUsage.coupon_id == coupon_id, CouponUsage.customer_id == customer_id)) or 0
    if coupon.usage_limit is not None and total_uses >= coupon.usage_limit:
        raise HTTPException(status_code=400, detail="Coupon usage limit has been reached")
    if coupon.per_customer_limit is not None and customer_uses >= coupon.per_customer_limit:
        raise HTTPException(status_code=400, detail="You have reached this coupon's usage limit")
    usage = CouponUsage(coupon_id=coupon_id, customer_id=customer_id, order_reference=order_reference)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage