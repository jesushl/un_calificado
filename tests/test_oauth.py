from app.config import get_settings
from app.main import app
from app.oauth import OAuthProfile, encode_state


def test_oauth_catalog_is_public():
    with app.test_client() as client:
        response = client.get("/api/v1/auth/oauth/providers")

    assert response.status_code == 200
    ids = [item["id"] for item in response.get_json()["items"]]
    assert ids == ["google", "facebook", "tiktok"]
    assert all(item["configured"] is False for item in response.get_json()["items"])


def test_oauth_start_without_keys_is_unavailable():
    with app.test_client() as client:
        response = client.get("/api/v1/auth/oauth/google")

    assert response.status_code == 503
    assert "correo" in response.get_json()["message"].lower()


def test_oauth_start_builds_google_url(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "google-client")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "google-secret")
    get_settings.cache_clear()
    try:
        with app.test_client() as client:
            response = client.get("/api/v1/auth/oauth/google?role=CLIENTE&next=/calificados/1")
        body = response.get_json()
        assert response.status_code == 200
        assert "accounts.google.com" in body["authorizationUrl"]
        assert "google-client" in body["authorizationUrl"]
        assert "state=" in body["authorizationUrl"]
    finally:
        get_settings.cache_clear()


def test_oauth_callback_issues_ticket_and_exchange(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "google-client")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "google-secret")
    get_settings.cache_clear()

    def fake_profile(provider, code):
        assert provider == "google"
        assert code == "auth-code"
        return OAuthProfile(
            provider="google",
            subject="google-sub-1",
            email="maria.google@example.com",
            name="María López",
        )

    monkeypatch.setattr("app.auth.fetch_profile", fake_profile)
    state = encode_state(
        {"provider": "google", "role": "CLIENTE", "next": "/calificados/abc", "ts": 9_999_999_999}
    )
    try:
        with app.test_client() as client:
            callback = client.get(
                f"/api/v1/auth/oauth/google/callback?code=auth-code&state={state}"
            )
            assert callback.status_code == 302
            location = callback.headers["Location"]
            assert "/entrar/oauth?code=" in location
            code = location.split("code=")[1].split("&")[0]
            exchanged = client.post("/api/v1/auth/oauth/exchange", json={"code": code})
            reused = client.post("/api/v1/auth/oauth/exchange", json={"code": code})

        assert exchanged.status_code == 200
        assert exchanged.get_json()["user"]["email"] == "maria.google@example.com"
        assert exchanged.get_json()["user"]["role"] == "CLIENTE"
        assert reused.status_code == 401
    finally:
        get_settings.cache_clear()


def test_oauth_dev_creates_session_in_test_env():
    with app.test_client() as client:
        response = client.post(
            "/api/v1/auth/oauth/facebook/dev",
            json={"email": "ana.facebook@example.com", "name": "Ana", "role": "PROVEEDOR"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "ana.facebook@example.com", "password": "whatever-long"},
        )

    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == "PROVEEDOR"
    assert login.status_code == 401
