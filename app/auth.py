from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, redirect, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .errors import ApiError, validation_error
from .models import Consent, RevokedToken, User, UserRole, UserStatus
from .oauth import (
    OAuthProfile,
    authorization_url,
    consume_ticket,
    fetch_profile,
    issue_ticket,
    provider_catalog,
    require_provider,
    safe_next_path,
    upsert_oauth_user,
)
from .config import get_settings
from .rate_limit import enforce_rate_limit
from .schemas import (
    AuthResponse,
    ConsentRequest,
    LoginRequest,
    OAuthExchange,
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
            or not user.password_hash
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


def _oauth_error_redirect(message: str) -> object:
    origin = get_settings().frontend_origin.rstrip("/")
    from urllib.parse import urlencode

    return redirect(f"{origin}/entrar?{urlencode({'oauth_error': message})}")


@router.get("/oauth/providers")
def oauth_providers():
    return jsonify({"items": provider_catalog()})


@router.get("/oauth/<provider>")
def start_oauth(provider: str):
    enforce_rate_limit("auth.oauth", limit=get_settings().auth_rate_limit)
    require_provider(provider)
    role = request.args.get("role") or "CLIENTE"
    if role not in {"CLIENTE", "PROVEEDOR"}:
        raise ApiError(400, "BAD_REQUEST", "El rol OAuth solo puede ser cliente o proveedor.")
    url = authorization_url(provider, role, safe_next_path(request.args.get("next")))
    return jsonify({"authorizationUrl": url, "provider": provider})


@router.get("/oauth/<provider>/callback")
def oauth_callback(provider: str):
    require_provider(provider)
    if request.args.get("error"):
        return _oauth_error_redirect("El acceso se canceló. Puedes entrar con correo y contraseña.")
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return _oauth_error_redirect("Faltó el código de acceso. Inténtalo de nuevo.")
    from .oauth import decode_state

    try:
        payload = decode_state(state)
        if payload.get("provider") != provider:
            raise ApiError(400, "BAD_REQUEST", "El estado OAuth no coincide.")
        profile = fetch_profile(provider, code)
        db = SessionLocal()
        try:
            user = upsert_oauth_user(db, profile, payload.get("role") or "CLIENTE")
            ticket = issue_ticket(db, user, payload.get("next"))
            db.commit()
        finally:
            db.close()
    except ApiError as error:
        return _oauth_error_redirect(error.message)
    origin = get_settings().frontend_origin.rstrip("/")
    from urllib.parse import urlencode

    query = {"code": ticket}
    if payload.get("next"):
        query["siguiente"] = payload["next"]
    return redirect(f"{origin}/entrar/oauth?{urlencode(query)}")


@router.post("/oauth/exchange")
def oauth_exchange():
    try:
        payload = OAuthExchange.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return _validation_response(error)
    db = SessionLocal()
    try:
        user, _next_path = consume_ticket(db, payload.code)
        token, expires_in = create_access_token(user)
        db.commit()
        response = AuthResponse(access_token=token, expires_in=expires_in, user=user)
        return jsonify(response.model_dump(mode="json"))
    finally:
        db.close()


@router.post("/oauth/<provider>/dev")
def oauth_dev(provider: str):
    if get_settings().app_env not in {"development", "test"}:
        raise ApiError(404, "NOT_FOUND", "No encontrado")
    require_provider(provider)
    body = request.get_json(silent=True) or {}
    email = str(body.get("email") or "").lower()
    if "@" not in email:
        raise ApiError(422, "VALIDATION_ERROR", "Escribe un correo electrónico.")
    role = body.get("role") or "CLIENTE"
    profile = OAuthProfile(
        provider=provider,
        subject=str(body.get("subject") or f"dev-{email}"),
        email=email,
        name=body.get("name"),
    )
    db = SessionLocal()
    try:
        user = upsert_oauth_user(db, profile, role)
        token, expires_in = create_access_token(user)
        db.commit()
        response = AuthResponse(access_token=token, expires_in=expires_in, user=user)
        return jsonify(response.model_dump(mode="json"))
    finally:
        db.close()
