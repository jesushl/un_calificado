from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, UserRole
from app.security import create_access_token, hash_password


def register(client, email, role="CLIENTE"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-password",
            "role": role,
            "privacy_consent_version": "2026-01",
            "adult_declaration": True,
        },
    )


def login(client, email):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-password"},
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def token_for(client, email, role="CLIENTE"):
    register(client, email, role)
    return login(client, email).get_json()["access_token"]


def admin_token():
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "admin@example.com"))
        if user is None:
            user = User(
                email="admin@example.com",
                password_hash=hash_password("correct-password"),
                role=UserRole.ADMINISTRADOR,
                privacy_consent_version="2026-01",
                adult_declaration=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token, _ = create_access_token(user)
        return token
    finally:
        db.close()
