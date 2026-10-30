"""OAuth para Google, Facebook y TikTok."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .errors import ApiError
from .models import OAuthIdentity, OAuthTicket, User, UserRole

OAUTH_PROVIDERS = ("google", "facebook", "tiktok")
_LABELS = {
    "google": "Google",
    "facebook": "Facebook",
    "tiktok": "TikTok",
}


@dataclass(frozen=True)
class OAuthProfile:
    provider: str
    subject: str
    email: str
    name: str | None


def provider_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": item,
            "label": _LABELS[item],
            "configured": is_configured(item),
        }
        for item in OAUTH_PROVIDERS
    ]


def is_configured(provider: str) -> bool:
    settings = get_settings()
    if provider == "google":
        return bool(settings.oauth_google_client_id and settings.oauth_google_client_secret)
    if provider == "facebook":
        return bool(
            settings.oauth_facebook_client_id and settings.oauth_facebook_client_secret
        )
    if provider == "tiktok":
        return bool(settings.oauth_tiktok_client_key and settings.oauth_tiktok_client_secret)
    return False


def require_provider(provider: str) -> str:
    if provider not in OAUTH_PROVIDERS:
        raise ApiError(400, "BAD_REQUEST", "Proveedor OAuth no soportado")
    return provider


def redirect_uri(provider: str) -> str:
    base = get_settings().oauth_redirect_base.rstrip("/")
    return f"{base}/api/v1/auth/oauth/{provider}/callback"


def encode_state(payload: dict[str, Any]) -> str:
    import hashlib
    import hmac
    from base64 import urlsafe_b64encode

    body = urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    secret = get_settings().jwt_secret.encode()
    signature = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def decode_state(state: str) -> dict[str, Any]:
    import hashlib
    import hmac
    from base64 import urlsafe_b64decode
    from datetime import datetime, timezone

    try:
        body, signature = state.split(".", 1)
    except ValueError as error:
        raise ApiError(400, "BAD_REQUEST", "El estado OAuth no es válido") from error
    secret = get_settings().jwt_secret.encode()
    expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ApiError(400, "BAD_REQUEST", "El estado OAuth no es válido")
    try:
        payload = json.loads(urlsafe_b64decode(body + "==").decode())
    except (ValueError, json.JSONDecodeError) as error:
        raise ApiError(400, "BAD_REQUEST", "El estado OAuth no es válido") from error
    issued = int(payload.get("ts") or 0)
    now = int(datetime.now(timezone.utc).timestamp())
    if now - issued > 600:
        raise ApiError(401, "UNAUTHORIZED", "El acceso OAuth venció. Inténtalo de nuevo.")
    return payload


def authorization_url(provider: str, role: str, next_path: str | None) -> str:
    from datetime import datetime, timezone

    require_provider(provider)
    if not is_configured(provider):
        raise ApiError(
            503,
            "OAUTH_UNAVAILABLE",
            f"El acceso con {_LABELS[provider]} aún no está listo. Entra con correo y contraseña.",
        )
    settings = get_settings()
    state = encode_state(
        {
            "provider": provider,
            "role": role,
            "next": next_path,
            "nonce": secrets.token_urlsafe(12),
            "ts": int(datetime.now(timezone.utc).timestamp()),
        }
    )
    callback = redirect_uri(provider)
    if provider == "google":
        query = urlencode(
            {
                "client_id": settings.oauth_google_client_id,
                "redirect_uri": callback,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    if provider == "facebook":
        query = urlencode(
            {
                "client_id": settings.oauth_facebook_client_id,
                "redirect_uri": callback,
                "response_type": "code",
                "scope": "email,public_profile",
                "state": state,
            }
        )
        return f"https://www.facebook.com/v21.0/dialog/oauth?{query}"
    query = urlencode(
        {
            "client_key": settings.oauth_tiktok_client_key,
            "redirect_uri": callback,
            "response_type": "code",
            "scope": "user.info.basic",
            "state": state,
        }
    )
    return f"https://www.tiktok.com/v2/auth/authorize/?{query}"


def _post_form(url: str, data: dict[str, str], headers: dict[str, str] | None = None) -> dict:
    payload = urlencode(data).encode()
    request = Request(url, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("Accept", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urlopen(request, timeout=12) as response:
        body = response.read().decode()
    return json.loads(body) if body else {}


def _get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    request = Request(url, method="GET")
    request.add_header("Accept", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urlopen(request, timeout=12) as response:
        body = response.read().decode()
    return json.loads(body) if body else {}


def fetch_profile(provider: str, code: str) -> OAuthProfile:
    settings = get_settings()
    callback = redirect_uri(provider)
    try:
        if provider == "google":
            token = _post_form(
                "https://oauth2.googleapis.com/token",
                {
                    "code": code,
                    "client_id": settings.oauth_google_client_id,
                    "client_secret": settings.oauth_google_client_secret,
                    "redirect_uri": callback,
                    "grant_type": "authorization_code",
                },
            )
            info = _get_json(
                "https://openidconnect.googleapis.com/v1/userinfo",
                {"Authorization": f"Bearer {token['access_token']}"},
            )
            email = (info.get("email") or "").lower()
            if not email:
                raise ApiError(
                    400,
                    "BAD_REQUEST",
                    "Google no nos mandó tu correo. Autoriza el correo o crea cuenta con contraseña.",
                )
            return OAuthProfile(
                provider="google",
                subject=str(info.get("sub")),
                email=email,
                name=info.get("name"),
            )
        if provider == "facebook":
            token = _get_json(
                "https://graph.facebook.com/v21.0/oauth/access_token?"
                + urlencode(
                    {
                        "client_id": settings.oauth_facebook_client_id,
                        "client_secret": settings.oauth_facebook_client_secret,
                        "redirect_uri": callback,
                        "code": code,
                    }
                )
            )
            info = _get_json(
                "https://graph.facebook.com/me?"
                + urlencode({"fields": "id,name,email", "access_token": token["access_token"]})
            )
            email = (info.get("email") or "").lower()
            if not email:
                raise ApiError(
                    400,
                    "BAD_REQUEST",
                    "Facebook no nos mandó tu correo. Autoriza el correo o crea cuenta con contraseña.",
                )
            return OAuthProfile(
                provider="facebook",
                subject=str(info.get("id")),
                email=email,
                name=info.get("name"),
            )
        token = _post_form(
            "https://open.tiktokapis.com/v2/oauth/token/",
            {
                "client_key": settings.oauth_tiktok_client_key,
                "client_secret": settings.oauth_tiktok_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": callback,
            },
        )
        info = _get_json(
            "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name",
            {"Authorization": f"Bearer {token['access_token']}"},
        )
        user = (info.get("data") or {}).get("user") or {}
        subject = str(user.get("open_id") or token.get("open_id") or "")
        if not subject:
            raise ApiError(401, "UNAUTHORIZED", "TikTok no devolvió el perfil.")
        email = f"tiktok.{subject}@oauth.uncalificado.local"
        return OAuthProfile(
            provider="tiktok",
            subject=subject,
            email=email,
            name=user.get("display_name"),
        )
    except ApiError:
        raise
    except Exception as error:
        raise ApiError(
            401,
            "UNAUTHORIZED",
            "No pudimos validar el acceso. Intenta de nuevo o entra con correo.",
        ) from error


def upsert_oauth_user(db: Session, profile: OAuthProfile, role: str) -> User:
    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == profile.provider,
            OAuthIdentity.subject == profile.subject,
        )
    )
    if identity is not None:
        user = db.get(User, identity.user_id)
        if user is None:
            raise ApiError(401, "UNAUTHORIZED", "La cuenta vinculada ya no existe.")
        if profile.name and not user.name:
            user.name = profile.name
        return user

    user = db.scalar(select(User).where(User.email == profile.email.lower()))
    if user is None:
        public_role = UserRole.PROVEEDOR if role == "PROVEEDOR" else UserRole.CLIENTE
        user = User(
            email=profile.email.lower(),
            password_hash=None,
            role=public_role,
            name=profile.name,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        db.add(user)
        db.flush()
    elif profile.name and not user.name:
        user.name = profile.name
    db.add(
        OAuthIdentity(
            user_id=user.id,
            provider=profile.provider,
            subject=profile.subject,
        )
    )
    db.flush()
    return user


def issue_ticket(db: Session, user: User, next_path: str | None) -> str:
    from .domain import utcnow

    ticket = OAuthTicket(
        code=secrets.token_urlsafe(24),
        user_id=user.id,
        expires_at=utcnow() + timedelta(minutes=2),
        next_path=next_path,
    )
    db.add(ticket)
    db.flush()
    return ticket.code


def _aware(value):
    from datetime import timezone

    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def consume_ticket(db: Session, code: str) -> tuple[User, str | None]:
    from .domain import utcnow

    ticket = db.get(OAuthTicket, code)
    if ticket is None or _aware(ticket.expires_at) < utcnow():
        if ticket is not None:
            db.delete(ticket)
            db.flush()
        raise ApiError(401, "UNAUTHORIZED", "El acceso OAuth venció. Inténtalo de nuevo.")
    user = db.get(User, ticket.user_id)
    next_path = ticket.next_path
    db.delete(ticket)
    db.flush()
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "La cuenta ya no está disponible.")
    return user, next_path


def safe_next_path(value: str | None) -> str | None:
    if not value or not value.startswith("/") or value.startswith("//"):
        return None
    if "://" in value:
        return None
    return value[:255]
