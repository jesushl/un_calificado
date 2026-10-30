from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings
from app.main import app


def register_payload(email="cliente@example.com", role="CLIENTE"):
    return {
        "email": email,
        "password": "correct-password",
        "role": role,
        "privacy_consent_version": "2026-01",
        "adult_declaration": True,
    }


def test_register_does_not_return_password_or_hash():
    with app.test_client() as client:
        response = client.post("/api/v1/auth/register", json=register_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert "password" not in body
    assert "password_hash" not in body
    assert body["email"] == "cliente@example.com"


def test_login_and_me_with_valid_token():
    with app.test_client() as client:
        client.post("/api/auth/register", json=register_payload())
        login = client.post(
            "/api/auth/login",
            json={"email": "cliente@example.com", "password": "correct-password"},
        )
        token = login.get_json()["access_token"]
        me = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert login.status_code == 200
    assert me.status_code == 200
    assert me.get_json()["email"] == "cliente@example.com"


def test_invalid_credentials_and_missing_token_are_rejected():
    with app.test_client() as client:
        client.post("/api/v1/auth/register", json=register_payload())
        invalid_login = client.post(
            "/api/v1/auth/login",
            json={"email": "cliente@example.com", "password": "wrong-password"},
        )
        missing_token = client.get("/api/v1/auth/me")

    assert invalid_login.status_code == 401
    assert missing_token.status_code == 401


def test_tampered_and_expired_tokens_are_rejected():
    with app.test_client() as client:
        client.post("/api/v1/auth/register", json=register_payload())
        token = client.post(
            "/api/v1/auth/login",
            json={"email": "cliente@example.com", "password": "correct-password"},
        ).get_json()["access_token"]
        header, claims, signature = token.split(".")
        replacement = "a" if signature[0] != "a" else "b"
        tampered = f"{header}.{claims}.{replacement}{signature[1:]}"
        expired = jwt.encode(
            {
                "sub": "00000000-0000-0000-0000-000000000000",
                "role": "CLIENTE",
                "iat": datetime.now(timezone.utc) - timedelta(minutes=2),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            get_settings().jwt_secret,
            algorithm=get_settings().jwt_algorithm,
        )
        tampered_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered}"},
        )
        expired_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )

    assert tampered_response.status_code == 401
    assert expired_response.status_code == 401


def test_role_guard_returns_forbidden_for_wrong_role():
    with app.test_client() as client:
        client.post("/api/v1/auth/register", json=register_payload())
        token = client.post(
            "/api/v1/auth/login",
            json={"email": "cliente@example.com", "password": "correct-password"},
        ).get_json()["access_token"]
        response = client.get(
            "/api/v1/auth/admin/ping",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
