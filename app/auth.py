from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .errors import validation_error
from .models import Consent, RevokedToken, User, UserRole, UserStatus
from .config import get_settings
from .rate_limit import enforce_rate_limit
from .schemas import (
    AuthResponse,
    ConsentRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from .security import (
    AuthenticationError,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)

router = Blueprint("auth", __name__)


def _validation_response(error: ValidationError):
    return jsonify({"detail": error.errors()}), 422


def _user_response(user: User) -> dict:
    return UserResponse.model_validate(user).model_dump(mode="json")


def register_user(payload: RegisterRequest, db: Session) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise ValueError("El correo ya está registrado")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        privacy_consent_version=payload.privacy_consent_version,
        adult_declaration=payload.adult_declaration,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("El correo ya está registrado") from None
    db.refresh(user)
    return user


@router.post("/register")
def register():
    enforce_rate_limit("auth.register", limit=get_settings().auth_rate_limit)
    try:
        payload = RegisterRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _validation_response(error)

    db = SessionLocal()
    try:
        try:
            user = register_user(payload, db)
        except ValueError as error:
            return jsonify({"detail": str(error)}), 409
        return jsonify(_user_response(user)), 201
    finally:
        db.close()


@router.post("/login")
def login():
    enforce_rate_limit("auth.login", limit=get_settings().auth_rate_limit)
    try:
        payload = LoginRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _validation_response(error)

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == payload.email.lower()))
        if (
            user is None
            or user.status != UserStatus.ACTIVE
            or not verify_password(payload.password, user.password_hash)
        ):
            return (
                jsonify({"detail": "Credenciales inválidas"}),
                401,
                {"WWW-Authenticate": "Bearer"},
            )

        token, expires_in = create_access_token(user)
        response = AuthResponse(access_token=token, expires_in=expires_in, user=user)
        return jsonify(response.model_dump(mode="json")), 200
    finally:
        db.close()


@router.get("/me")
def me():
    try:
        return jsonify(_user_response(get_current_user()))
    except AuthenticationError:
        return jsonify({"detail": "Credenciales inválidas o token ausente"}), 401


@router.post("/consents")
def create_consent():
    try:
        payload = ConsentRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)

    current_user = get_current_user()
    db = SessionLocal()
    try:
        user = db.get(User, current_user.id)
        consent = Consent(
            user_id=user.id,
            privacy_version=payload.privacy_version,
            adult_declaration=payload.adult_declaration,
        )
        user.privacy_consent_version = payload.privacy_version
        user.adult_declaration = payload.adult_declaration
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return (
            jsonify(
                {
                    "id": str(consent.id),
                    "privacyVersion": consent.privacy_version,
                    "acceptedAt": consent.accepted_at.isoformat(),
                }
            ),
            201,
        )
    finally:
        db.close()


@router.post("/logout")
def logout():
    current_user = get_current_user()
    jti = getattr(g, "token_jti", None)
    exp = getattr(g, "token_exp", None)
    if jti:
        db = SessionLocal()
        try:
            expires_at = (
                datetime.fromtimestamp(int(exp), tz=timezone.utc)
                if exp
                else datetime.now(timezone.utc)
            )
            db.merge(
                RevokedToken(jti=jti, user_id=current_user.id, expires_at=expires_at)
            )
            db.commit()
        finally:
            db.close()
    return ("", 204)


@router.get("/admin/ping")
@require_roles(UserRole.ADMINISTRADOR)
def admin_ping():
    current_user = get_current_user()
    return {"status": "ok", "user_id": str(current_user.id)}
