from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from .database import SessionLocal
from .errors import validation_error
from .models import User
from .schemas import UserUpdateRequest
from .security import get_current_user

router = Blueprint("users", __name__)


def serialize_user(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "status": user.status.value,
        "privacy_consent_version": user.privacy_consent_version,
        "created_at": user.created_at.isoformat(),
        "name": user.name,
        "phone": user.phone,
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
        db.commit()
        db.refresh(user)
        return jsonify(serialize_user(user))
    finally:
        db.close()
