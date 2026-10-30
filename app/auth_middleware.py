from uuid import uuid4

from flask import g, jsonify, request
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import UserRole
from .route_policy import ROLE_POLICY, is_public_route
from .security import AuthenticationError, user_from_token


def _policy_for(method: str, path: str) -> set[UserRole] | None:
    exact = ROLE_POLICY.get(f"{method} {path}")
    if exact is not None:
        return exact

    for key, roles in ROLE_POLICY.items():
        policy_method, policy_path = key.split(" ", 1)
        if policy_method != method:
            continue
        expected = policy_path.split("/")
        actual = path.split("/")
        if len(expected) == len(actual) and all(
            left == right or left.startswith("{")
            for left, right in zip(expected, actual)
        ):
            return roles
    return None


def register_auth_middleware(app):
    """Registra autenticación JWT y autorización RBAC antes de cada request."""

    @app.before_request
    def authenticate_request():
        g.request_id = request.headers.get("X-Request-Id", str(uuid4()))
        method = request.method.upper()
        path = request.path
        if method == "OPTIONS":
            return ("", 204)
        if is_public_route(method, path):
            return None
        if not path.startswith("/api"):
            return None

        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return (
                jsonify({"detail": "Credenciales inválidas o token ausente"}),
                401,
                {"WWW-Authenticate": "Bearer"},
            )

        db: Session = SessionLocal()
        try:
            try:
                user = user_from_token(token, db)
            except AuthenticationError:
                return (
                    jsonify({"detail": "Credenciales inválidas o token ausente"}),
                    401,
                    {"WWW-Authenticate": "Bearer"},
                )

            allowed_roles = _policy_for(method, path)
            if allowed_roles is None or user.role not in allowed_roles:
                return jsonify({"detail": "El rol no tiene permiso para esta ruta"}), 403
            g.current_user = user
            return None
        finally:
            db.close()
