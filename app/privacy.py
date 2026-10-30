from datetime import timedelta
from uuid import uuid4

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select

from .catalog import ACTIVE_PROJECT_STATUSES
from .database import SessionLocal
from .domain import parse_uuid, utcnow
from .errors import ApiError, validation_error
from .models import (
    AvailabilityIncident,
    PrivacyRequest,
    PrivacyStatus,
    ProjectStatus,
    ServiceRequest,
    StoredFile,
    User,
    UserRole,
    UserStatus,
)
from .schemas import PrivacyFulfillment, PrivacyRequestCreate
from .security import get_current_user
from .storage import verify_signed_download

privacy = Blueprint("privacy", __name__)
admin = Blueprint("admin", __name__)
files = Blueprint("files", __name__)


def _serialize_privacy(item: PrivacyRequest) -> dict:
    return {
        "folio": item.folio,
        "type": item.request_type.value,
        "status": item.status.value,
        "createdAt": item.created_at.isoformat(),
        "respondedAt": item.responded_at.isoformat() if item.responded_at else None,
    }


@privacy.post("/requests")
def create_privacy_request():
    try:
        payload = PrivacyRequestCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        item = PrivacyRequest(
            folio=f"ARCO-{utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}",
            user_id=user.id,
            request_type=payload.type,
            corrected_values=payload.correctedValues,
            due_at=utcnow() + timedelta(days=20),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return jsonify(_serialize_privacy(item)), 201
    finally:
        db.close()


@privacy.post("/requests/<folio>/fulfillment")
def fulfill_privacy_request(folio: str):
    try:
        payload = PrivacyFulfillment.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    actor = get_current_user()
    if actor.role != UserRole.ADMINISTRADOR:
        raise ApiError(403, "FORBIDDEN", "Solo un administrador atiende ARCO")
    db = SessionLocal()
    try:
        item = db.scalar(select(PrivacyRequest).where(PrivacyRequest.folio == folio))
        if item is None:
            raise ApiError(404, "NOT_FOUND", "Solicitud ARCO no encontrada")
        user = db.get(User, item.user_id)
        if payload.action == "ANONIMIZAR":
            active = db.scalar(
                select(ServiceRequest).where(
                    ServiceRequest.owner_id == user.id,
                    ServiceRequest.status.in_(
                        [ProjectStatus(status) for status in ACTIVE_PROJECT_STATUSES]
                    ),
                )
            )
            if active is not None:
                item.status = PrivacyStatus.BLOQUEADA
                db.commit()
                raise ApiError(409, "CONFLICT", "Anonimización bloqueada por proyecto activo")
            item.previous_values = {"email": user.email, "name": user.name, "phone": user.phone}
            user.email = f"anonimizado-{user.id}@invalid.example"
            user.name = None
            user.phone = None
            user.status = UserStatus.DISABLED
        elif payload.action == "RECTIFICAR":
            values = payload.corrected_values or item.corrected_values or {}
            item.previous_values = {"name": user.name, "phone": user.phone}
            if "name" in values:
                user.name = values["name"]
            if "phone" in values:
                user.phone = values["phone"]
        item.status = PrivacyStatus.RESPONDIDA
        item.responded_at = utcnow()
        item.response_note = payload.response_note
        db.commit()
        db.refresh(item)
        return jsonify(_serialize_privacy(item))
    finally:
        db.close()


@admin.get("/availability-reports")
def availability_report():
    month = request.args.get("month")
    if not month or len(month) != 7:
        raise ApiError(422, "VALIDATION_ERROR", "month debe tener formato YYYY-MM")
    db = SessionLocal()
    try:
        incidents = list(
            db.scalars(select(AvailabilityIncident).where(AvailabilityIncident.month == month))
        )
        unplanned = [row.details | {"title": row.title} for row in incidents if row.kind == "UNPLANNED"]
        planned = [row.details | {"title": row.title} for row in incidents if row.kind != "UNPLANNED"]
        downtime_hours = sum(
            ((row.ended_at or utcnow()) - row.started_at).total_seconds() / 3600
            for row in incidents
            if row.started_at
        )
        availability = max(0, round(100 - (downtime_hours / (24 * 30) * 100), 2))
        return jsonify(
            {
                "month": month,
                "availabilityPercent": availability if incidents else 100,
                "unplannedOutages": unplanned,
                "plannedMaintenanceNotices": planned,
            }
        )
    finally:
        db.close()


@files.get("/<file_id>/content")
def download_file(file_id: str):
    get_current_user()
    db = SessionLocal()
    try:
        stored = db.get(StoredFile, parse_uuid(file_id, "fileId"))
        if stored is None:
            raise ApiError(404, "NOT_FOUND", "Archivo no encontrado")
        if not verify_signed_download(
            file_id,
            stored.object_key,
            request.args.get("exp", ""),
            request.args.get("sig", ""),
        ):
            raise ApiError(403, "FORBIDDEN", "La URL temporal no es válida")
        return jsonify(
            {
                "objectKey": stored.object_key,
                "contentType": stored.mime_type,
                "message": "El binario vive en object storage; esta URL solo autoriza la descarga temporal.",
            }
        )
    finally:
        db.close()
