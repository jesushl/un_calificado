from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .catalog import ALLOWED_TRADES
from .database import SessionLocal
from .domain import (
    is_complete_provider,
    is_verified,
    parse_uuid,
    rating_summary,
    serialize_file,
    serialize_request,
)
from .errors import ApiError, validation_error
from .models import (
    FileType,
    ProjectStatus,
    Provider,
    ServiceRequest,
    StoredFile,
    UserRole,
)
from .schemas import ContactRequest, PageQuery, page_info
from .security import get_current_user

router = Blueprint("explore", __name__)
PUBLIC_WORK_STATUSES = {ProjectStatus.TERMINADO, ProjectStatus.CONCLUIDO}


def _concluded_count(db: Session, provider_id) -> int:
    return db.scalar(
        select(func.count()).select_from(ServiceRequest).where(
            ServiceRequest.selected_provider_id == provider_id,
            ServiceRequest.status.in_(PUBLIC_WORK_STATUSES),
        )
    ) or 0


def serialize_explore_provider(provider: Provider, db: Session) -> dict:
    cover = next(
        (item for item in provider.portfolio_files if item.file_type == FileType.IMAGE),
        None,
    )
    payload = {
        "id": str(provider.id),
        "name": provider.name,
        "modality": provider.modality.value,
        "trades": [item.trade for item in provider.trades],
        "coverage": [item.zone for item in provider.coverage],
        "experienceYears": provider.experience_years,
        "generalAvailability": provider.general_availability,
        "verified": is_verified(provider),
        "rating": rating_summary(db, provider.id),
        "concludedCount": _concluded_count(db, provider.id),
        "coverImage": serialize_file(cover) if cover else None,
    }
    return payload


def _popular_sort(provider: Provider, db: Session):
    rating = rating_summary(db, provider.id)
    return (-rating["average"], -rating["count"], -_concluded_count(db, provider.id))


@router.get("/providers")
def list_popular_providers():
    pagination = PageQuery.model_validate(request.args.to_dict())
    oficio = request.args.get("oficio")
    db = SessionLocal()
    try:
        providers = [
            provider
            for provider in db.scalars(select(Provider)).all()
            if is_complete_provider(provider)
            and (not oficio or oficio in {item.trade for item in provider.trades})
        ]
        providers.sort(key=lambda item: _popular_sort(item, db))
        start = (pagination.page - 1) * pagination.page_size
        page_items = providers[start : start + pagination.page_size]
        return jsonify(
            {
                "items": [serialize_explore_provider(item, db) for item in page_items],
                "page": page_info(pagination.page, pagination.page_size, len(providers)),
            }
        )
    finally:
        db.close()


@router.get("/providers/<provider_id>")
def get_public_provider(provider_id: str):
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None or not is_complete_provider(provider):
            raise ApiError(404, "NOT_FOUND", "No encontramos a ese calificado.")
        return jsonify(serialize_explore_provider(provider, db))
    finally:
        db.close()


@router.post("/providers/<provider_id>")
def contact_provider(provider_id: str):
    try:
        payload = ContactRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    if user.role != UserRole.CLIENTE:
        raise ApiError(403, "FORBIDDEN", "Solo un cliente con cuenta puede contactar a un calificado.")
    if payload.trade and payload.trade not in ALLOWED_TRADES:
        raise ApiError(422, "VALIDATION_ERROR", "oficio fuera del catálogo")
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None or not is_complete_provider(provider):
            raise ApiError(404, "NOT_FOUND", "No encontramos a ese calificado.")
        trade = payload.trade or next((item.trade for item in provider.trades), None)
        if not trade:
            raise ApiError(422, "VALIDATION_ERROR", "El calificado no tiene oficio público.")
        item = ServiceRequest(
            owner_id=user.id,
            selected_provider_id=provider.id,
            expected_outcome=payload.expected_outcome,
            trade=trade,
            approximate_zone=payload.approximate_zone,
            description=f"Contacto iniciado desde la ficha de {provider.name}.",
            manual_capture=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item)), 201
    finally:
        db.close()


def _work_from_file(stored: StoredFile, db: Session) -> dict | None:
    if stored.file_type != FileType.IMAGE:
        return None
    request_item = stored.request
    provider = stored.provider
    if request_item is None or request_item.status not in PUBLIC_WORK_STATUSES:
        return None
    provider = request_item.selected_provider
    if provider is None or not is_complete_provider(provider):
        return None
    signed = serialize_file(stored)
    return {
        "id": signed["id"],
        "fileName": signed["fileName"],
        "contentType": signed["contentType"],
        "downloadUrl": signed["downloadUrl"],
        "downloadUrlExpiresAt": signed["downloadUrlExpiresAt"],
        "trade": request_item.trade,
        "expectedOutcome": request_item.expected_outcome,
        "approximateZone": request_item.approximate_zone,
        "provider": serialize_explore_provider(provider, db),
    }


@router.get("/works")
def list_public_works():
    pagination = PageQuery.model_validate(request.args.to_dict())
    oficio = request.args.get("oficio")
    db = SessionLocal()
    try:
        files = db.scalars(
            select(StoredFile).where(StoredFile.file_type == FileType.IMAGE)
        ).all()
        works = []
        for stored in files:
            item = _work_from_file(stored, db)
            if item is None:
                continue
            if oficio and item["trade"] != oficio:
                continue
            works.append(item)
        works.sort(key=lambda item: (-item["provider"]["rating"]["average"], item["fileName"]))
        start = (pagination.page - 1) * pagination.page_size
        page_items = works[start : start + pagination.page_size]
        return jsonify(
            {
                "items": page_items,
                "page": page_info(pagination.page, pagination.page_size, len(works)),
            }
        )
    finally:
        db.close()
