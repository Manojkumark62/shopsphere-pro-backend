
from getpass import getpass
from app.database.connection import SessionLocal
from app.models.auth import User, UserRole
from app.core.security import hash_password

db = SessionLocal()
try:
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password: ")
    if len(password) < 12:
        raise ValueError("Admin password must contain at least 12 characters")
    if db.query(User).filter(User.email == email).first():
        raise ValueError("Email already exists")
    admin = User(email=email, password_hash=hash_password(password), role=UserRole.ADMIN, is_active=True)
    db.add(admin)
    db.commit()
    print("Admin account created successfully")
except Exception:
    db.rollback()
    raise
finally:
    db.close()
