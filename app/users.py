from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select

from .database import SessionLocal
from .errors import validation_error
from .geo import canonical_zone, clamp_radius
from .models import Provider, User, UserRole
from .schemas import UserUpdateRequest
from .security import get_current_user

router = Blueprint("users", __name__)


def _display_name(user: User, db=None) -> str | None:
    if user.name and user.name.strip():
        return user.name.strip()
    if user.role == UserRole.PROVEEDOR:
        owns_session = db is None
        session = db or SessionLocal()
        try:
            provider = session.scalar(select(Provider).where(Provider.account_id == user.id))
            if provider and provider.name:
                return provider.name
        finally:
            if owns_session:
                session.close()
    return None


def serialize_user(user, db=None) -> dict:
    display = _display_name(user, db)
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "status": user.status.value,
        "privacy_consent_version": user.privacy_consent_version,
        "created_at": user.created_at.isoformat(),
        "name": display or user.name,
        "phone": user.phone,
        "searchZone": user.search_zone,
        "search_zone": user.search_zone,
        "maxDistanceKm": user.max_distance_km,
        "max_distance_km": user.max_distance_km,
    }


@router.get("/me")
def get_me():
    return jsonify(serialize_user(get_current_user()))


@router.patch("/me")
def patch_me():
    try:
        payload = UserUpdateRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)

    db = SessionLocal()
    try:
        user = db.get(User, get_current_user().id)
        if payload.name is not None:
            user.name = payload.name
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.search_zone is not None:
            user.search_zone = canonical_zone(payload.search_zone)
        if payload.max_distance_km is not None:
            user.max_distance_km = clamp_radius(payload.max_distance_km)
        db.commit()
        db.refresh(user)
        return jsonify(serialize_user(user))
    finally:
        db.close()
