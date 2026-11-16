
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.customer_registration import CustomerRegisterRequest, CustomerRegistrationResponse, EmailVerificationResponse
from app.services.registration_service import register_customer, verify_customer_email

router = APIRouter(prefix="/api/v1/registration", tags=["Customer Registration"])

@router.post("/register", response_model=CustomerRegistrationResponse, status_code=201)
def register(data: CustomerRegisterRequest, db: Session = Depends(get_db)):
    return register_customer(db, data)

@router.get("/verify-email", response_model=EmailVerificationResponse)
def verify_email(token: str = Query(min_length=20), db: Session = Depends(get_db)):
    return verify_customer_email(db, token)
