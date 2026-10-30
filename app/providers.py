from datetime import date

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .domain import (
    expire_pending_entities,
    is_complete_provider,
    is_verified,
    parse_uuid,
    provider_of,
    rating_summary,
    serialize_file,
    serialize_provider,
    utcnow,
)
from .geo import canonical_zone, clamp_radius, within_radius
from .errors import ApiError, validation_error
from .models import (
    FileType,
    Provider,
    ProviderCoverage,
    ProviderModality,
    ProviderTrade,
    ProviderUnavailableDate,
    StoredFile,
    UserRole,
    Verification,
    VerificationStatus,
)
from .schemas import (
    FileUploadRequest,
    PageQuery,
    ProviderUpsertRequest,
    VerificationRequest,
    page_info,
)
from .security import get_current_user

router = Blueprint("providers", __name__)


def _sync_profile(provider: Provider, payload: ProviderUpsertRequest) -> None:
    provider.name = payload.name
    provider.modality = ProviderModality(payload.modality)
    provider.experience_years = payload.experience_years
    provider.general_availability = payload.general_availability
    provider.address = payload.address
    provider.reference_price_mxn = payload.reference_price_mxn
    provider.guarantee_months = payload.guarantee_months
    provider.updated_at = utcnow()
    provider.trades.clear()
    provider.coverage.clear()
    provider.unavailable_dates.clear()
    for trade in payload.trades:
        provider.trades.append(ProviderTrade(trade=trade))
    for zone in payload.coverage:
        provider.coverage.append(ProviderCoverage(zone=zone))
    for day in payload.unavailable_dates:
        provider.unavailable_dates.append(ProviderUnavailableDate(day=day))


def _matches_filters(provider: Provider, args, db: Session) -> bool:
    oficio = args.get("oficio")
    zona = args.get("zona")
    fecha = args.get("fecha")
    verificado = args.get("verificado")
    experiencia = args.get("experienciaSimilar")
    precio_min = args.get("precioMin")
    precio_max = args.get("precioMax")
    trades = {item.trade for item in provider.trades}
    zones = {item.zone.lower() for item in provider.coverage}
    if oficio and oficio not in trades:
        return False
    if zona and zona.lower() not in zones:
        return False
    if fecha:
        day = date.fromisoformat(fecha)
        if any(item.day == day for item in provider.unavailable_dates):
            return False
    if verificado is not None:
        wanted = str(verificado).lower() == "true"
        if is_verified(provider) != wanted:
            return False
    if experiencia is not None and str(experiencia).lower() == "true":
        if rating_summary(db, provider.id)["count"] == 0:
            return False
    price = float(provider.reference_price_mxn) if provider.reference_price_mxn is not None else None
    if precio_min and (price is None or price < float(precio_min)):
        return False
    if precio_max and (price is None or price > float(precio_max)):
        return False
    return True


def _sort_key(provider: Provider, db: Session, sort: str | None, zona: str | None):
    rating = rating_summary(db, provider.id)["average"]
    price = float(provider.reference_price_mxn or 10**9)
    available = 0 if provider.general_availability else 1
    nearby = 0 if zona and any(zona.lower() == item.zone.lower() for item in provider.coverage) else 1
    guarantee = -(provider.guarantee_months or 0)
    if sort in {"calificacion", "rating"}:
        return (-rating, nearby, price)
    if sort in {"precio", "price"}:
        return (price, -rating)
    if sort in {"disponibilidad", "availability"}:
        return (available, -rating)
    if sort in {"cercania", "proximity"}:
        return (nearby, -rating)
    if sort in {"garantia", "guarantee"}:
        return (guarantee, -rating)
    return (nearby, -rating, price)


@router.get("")
def list_providers():
    user = get_current_user()
    pagination = PageQuery.model_validate(request.args.to_dict())
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        origin = canonical_zone(request.args.get("zona")) or canonical_zone(user.search_zone)
        radius = clamp_radius(user.max_distance_km)
        providers = []
        for provider in db.scalars(select(Provider)).all():
            if not is_complete_provider(provider) or not _matches_filters(
                provider, request.args, db
            ):
                continue
            nearby, _distance = within_radius(
                origin, radius, [item.zone for item in provider.coverage]
            )
            if origin and not nearby:
                continue
            providers.append(provider)
        providers.sort(
            key=lambda item: _sort_key(
                item, db, request.args.get("ordenarPor"), origin
            )
        )
        start = (pagination.page - 1) * pagination.page_size
        page_items = providers[start : start + pagination.page_size]
        return jsonify(
            {
                "items": [serialize_provider(item, db, user) for item in page_items],
                "page": page_info(pagination.page, pagination.page_size, len(providers)),
                "noResultsMessage": None
                if providers
                else "No hay proveedores que coincidan con oficio, zona y fecha.",
            }
        )
    finally:
        db.close()


@router.post("")
def create_provider():
    try:
        payload = ProviderUpsertRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        if provider_of(user, db) is not None:
            raise ApiError(400, "BAD_REQUEST", "El proveedor ya tiene un perfil")
        provider = Provider(account_id=user.id)
        _sync_profile(provider, payload)
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return jsonify(serialize_provider(provider, db, user)), 201
    finally:
        db.close()


@router.get("/<provider_id>")
def get_provider(provider_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        return jsonify(serialize_provider(provider, db, user))
    finally:
        db.close()


@router.put("/<provider_id>")
def replace_provider(provider_id: str):
    try:
        payload = ProviderUpsertRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        if provider.account_id != user.id:
            raise ApiError(403, "FORBIDDEN", "Solo el dueño puede actualizar el perfil")
        _sync_profile(provider, payload)
        db.commit()
        db.refresh(provider)
        return jsonify(serialize_provider(provider, db, user))
    finally:
        db.close()


@router.get("/<provider_id>/portfolio")
def list_portfolio(provider_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        files = [item for item in provider.portfolio_files]
        return jsonify(
            {
                "items": [serialize_file(item) for item in files],
                "page": page_info(1, max(len(files), 1), len(files)),
            }
        )
    finally:
        db.close()


@router.post("/<provider_id>/portfolio")
def add_portfolio(provider_id: str):
    try:
        payload = FileUploadRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        if provider.account_id != user.id:
            raise ApiError(403, "FORBIDDEN", "Solo el dueño puede cargar el portafolio")
        stored = StoredFile(
            provider_id=provider.id,
            owner_id=user.id,
            file_type=FileType.IMAGE if payload.content_type.startswith("image/") else FileType.VIDEO,
            file_name=payload.file_name,
            object_key=payload.object_key,
            mime_type=payload.content_type,
            size_bytes=payload.size_bytes,
        )
        db.add(stored)
        db.commit()
        db.refresh(stored)
        return jsonify(serialize_file(stored)), 201
    finally:
        db.close()


@router.post("/<provider_id>/verifications")
def submit_verification(provider_id: str):
    try:
        payload = VerificationRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        if provider.account_id != user.id:
            raise ApiError(403, "FORBIDDEN", "Solo el dueño puede enviar verificación")
        file = db.get(StoredFile, payload.fileId)
        if file is None or file.provider_id != provider.id:
            raise ApiError(422, "VALIDATION_ERROR", "La evidencia no pertenece al perfil")
        verification = Verification(
            provider_id=provider.id,
            verification_type=payload.type,
            status=VerificationStatus.PENDIENTE,
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return (
            jsonify(
                {
                    "id": str(verification.id),
                    "type": verification.verification_type,
                    "status": verification.status.value,
                    "reason": verification.reason,
                    "reviewedAt": None,
                }
            ),
            201,
        )
    finally:
        db.close()


@router.patch("/<provider_id>/verifications/<verification_id>")
def review_verification(provider_id: str, verification_id: str):
    user = get_current_user()
    if user.role != UserRole.ADMINISTRADOR:
        raise ApiError(403, "FORBIDDEN", "Solo un administrador revisa verificaciones")
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in {"VERIFICADA", "RECHAZADA", "RETIRADA"}:
        raise ApiError(422, "VALIDATION_ERROR", "Estado de verificación inválido")
    db = SessionLocal()
    try:
        provider = db.get(Provider, parse_uuid(provider_id, "providerId"))
        verification = db.get(Verification, parse_uuid(verification_id, "verificationId"))
        if provider is None or verification is None or verification.provider_id != provider.id:
            raise ApiError(404, "NOT_FOUND", "Verificación no encontrada")
        verification.status = VerificationStatus(status)
        verification.reason = body.get("reason")
        verification.reviewed_at = utcnow()
        db.commit()
        db.refresh(verification)
        return jsonify(
            {
                "type": verification.verification_type,
                "status": verification.status.value,
                "reason": verification.reason,
                "reviewedAt": verification.reviewed_at.isoformat(),
            }
        )
    finally:
        db.close()
