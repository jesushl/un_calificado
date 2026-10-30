from app.main import app
from tests.helpers import auth_header, login, register, token_for


def test_consent_logout_and_user_patch():
    with app.test_client() as client:
        token = token_for(client, "cliente@example.com")
        consent = client.post(
            "/api/v1/auth/consents",
            headers=auth_header(token),
            json={"privacyVersion": "2026-02", "adultDeclaration": True},
        )
        patched = client.patch(
            "/api/v1/users/me",
            headers=auth_header(token),
            json={"name": "Ana Cliente", "phone": "5550001111"},
        )
        logout = client.post("/api/v1/auth/logout", headers=auth_header(token))
        me = client.get("/api/v1/auth/me", headers=auth_header(token))

    assert consent.status_code == 201
    assert consent.get_json()["privacyVersion"] == "2026-02"
    assert patched.status_code == 200
    assert patched.get_json()["name"] == "Ana Cliente"
    assert logout.status_code == 204
    assert me.status_code == 401


def test_register_still_rejects_duplicate_email_with_409():
    with app.test_client() as client:
        register(client, "dup@example.com")
        again = register(client, "dup@example.com")

    assert again.status_code == 409
