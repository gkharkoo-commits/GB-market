import argparse
import getpass
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.permissions import UserRole
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.user import User

def create_admin():
    parser = argparse.ArgumentParser(description="Securely create an Administrator for GB MARKET.")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--phone", help="Administrator mobile number")
    parser.add_argument("--name", help="Administrator full name")
    parser.add_argument("--password", help="Administrator password (prompted securely if omitted)")

    args = parser.parse_args()

    email = args.email or settings.INITIAL_ADMIN_EMAIL
    phone = args.phone or settings.INITIAL_ADMIN_PHONE
    name = args.name or settings.INITIAL_ADMIN_NAME

    print("==================================================")
    print(" GB MARKET — Secure Administrator Account Creator ")
    print("==================================================")
    print(f"Creating / Updating Admin: {name} ({email}, {phone})")

    password = args.password
    if not password:
        password = getpass.getpass("Enter secure password (min 8 chars): ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match!")
            sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter((User.email == email) | (User.phone == phone)).first()
        if user:
            print(f"Existing user found with id={user.id}. Updating to Administrator role...")
            user.full_name = name
            user.role = UserRole.ADMIN.value
            user.hashed_password = hash_password(password)
            user.is_active = True
            user.is_verified = True
        else:
            user = User(
                email=email.lower().strip(),
                phone=phone.strip(),
                full_name=name.strip(),
                hashed_password=hash_password(password),
                role=UserRole.ADMIN.value,
                is_active=True,
                is_verified=True,
            )
            db.add(user)

        db.commit()
        db.refresh(user)
        print(f"SUCCESS: Administrator account '{user.email}' (ID: {user.id}) configured successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
