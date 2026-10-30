from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import UUID, uuid4

import bcrypt
import jwt
from flask import g, jsonify
from sqlalchemy.orm import Session

from .config import get_settings
from .models import RevokedToken, User, UserRole, UserStatus


class AuthenticationError(Exception):
    """Error controlado para credenciales ausentes, inválidas o expiradas."""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.jwt_expiration)
    expires_at = now + expires_delta
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, int(expires_delta.total_seconds())


def authentication_error() -> AuthenticationError:
    return AuthenticationError("Credenciales inválidas o token ausente")


def _decode_token(token: str) -> dict:
    settings = get_settings()
    secrets = [settings.jwt_secret]
    if settings.jwt_secret_previous:
        secrets.append(settings.jwt_secret_previous)
    last_error: Exception | None = None
    for secret in secrets:
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=[settings.jwt_algorithm],
                options={"require": ["sub", "role", "iat", "exp"]},
            )
        except jwt.InvalidTokenError as error:
            last_error = error
    raise last_error or jwt.InvalidTokenError("token inválido")


def user_from_token(token: str, db: Session) -> User:
    try:
        payload = _decode_token(token)
        user_id = UUID(payload["sub"])
        token_role = UserRole(payload["role"])
        jti = payload.get("jti")
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise authentication_error() from None

    if jti and db.get(RevokedToken, jti) is not None:
        raise authentication_error()

    user = db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE or user.role != token_role:
        raise authentication_error()
    g.token_jti = jti
    g.token_exp = payload.get("exp")
    return user


def get_current_user() -> User:
    """Obtiene el usuario autenticado que el middleware guardó en Flask g."""
    current_user = getattr(g, "current_user", None)
    if current_user is None:
        raise authentication_error()
    return current_user


def optional_user() -> User | None:
    return getattr(g, "current_user", None)


def require_roles(*allowed_roles: UserRole):
    """Decorador Flask para reforzar permisos en una vista específica."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                current_user = get_current_user()
            except AuthenticationError:
                return (
                    jsonify({"detail": "Credenciales inválidas o token ausente"}),
                    401,
                )
            if current_user.role not in allowed_roles:
                return (
                    jsonify({"detail": "El rol no tiene permiso para esta ruta"}),
                    403,
                )
            return view(*args, **kwargs)

        return wrapped

    return decorator
