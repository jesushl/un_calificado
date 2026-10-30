from datetime import timedelta, timezone

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .catalog import STATUS_TRANSITIONS
from .database import SessionLocal
from .domain import (
    append_audit,
    contains_phone,
    expire_pending_entities,
    get_request_or_404,
    has_accepted_proposal,
    is_complete_provider,
    is_verified,
    location_visibility,
    parse_uuid,
    provider_of,
    rating_summary,
    require_owner,
    require_request_access,
    serialize_file,
    serialize_provider,
    serialize_request,
    strip_phones,
    utcnow,
)
from .errors import ApiError, validation_error
from .models import (
    Appointment,
    AppointmentStatus,
    AuditEvent,
    Evaluation,
    EvaluationStatus,
    EvaluationSubject,
    FileType,
    Message,
    ProjectStatus,
    Provider,
    RequestRejection,
    ServiceRequest,
    StoredFile,
    SupportCase,
    SupportStatus,
    User,
    UserRole,
    VisualRepresentation,
    VisualStatus,
)
from .schemas import (
    EvaluationCreate,
    FileUploadRequest,
    PageQuery,
    RequestCreate,
    RequestPatch,
    SearchRequest,
    StatusPatch,
    page_info,
)
from .security import get_current_user

router = Blueprint("projects", __name__)


def _owned_or_assigned(db: Session, user: User) -> list[ServiceRequest]:
    provider = provider_of(user, db)
    query = select(ServiceRequest)
    if user.role == UserRole.ADMINISTRADOR:
        return list(db.scalars(query))
    if user.role == UserRole.PROVEEDOR and provider is not None:
        return list(
            db.scalars(
                query.where(
                    (ServiceRequest.owner_id == user.id)
                    | (ServiceRequest.selected_provider_id == provider.id)
                )
            )
        )
    return list(db.scalars(query.where(ServiceRequest.owner_id == user.id)))


def _ready_for_search(item: ServiceRequest) -> list[str]:
    missing = []
    if not item.trade:
        missing.append("trade")
    if not item.approximate_zone:
        missing.append("approximateZone")
    if item.desired_date is None:
        missing.append("desiredDate")
    if not item.description:
        missing.append("description")
    return missing


@router.get("")
def list_requests():
    user = get_current_user()
    pagination = PageQuery.model_validate(request.args.to_dict())
    estado = request.args.get("estado")
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        items = _owned_or_assigned(db, user)
        if estado:
            items = [item for item in items if item.status.value == estado]
        items.sort(key=lambda item: item.created_at, reverse=True)
        start = (pagination.page - 1) * pagination.page_size
        page_items = items[start : start + pagination.page_size]
        return jsonify(
            {
                "items": [serialize_request(item) for item in page_items],
                "page": page_info(pagination.page, pagination.page_size, len(items)),
            }
        )
    finally:
        db.close()


@router.post("")
def create_request():
    try:
        payload = RequestCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        item = ServiceRequest(
            owner_id=user.id,
            expected_outcome=payload.expected_outcome,
            trade=payload.trade,
            approximate_zone=payload.approximate_zone,
            desired_date=payload.desired_date,
            description=payload.description,
            ai_conversation_id=payload.ai_conversation_id,
            manual_capture=payload.manual_capture,
            status=ProjectStatus.BORRADOR,
        )
        db.add(item)
        db.flush()
        append_audit(db, item, user.id, "SOLICITUD_CREADA")
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item)), 201
    finally:
        db.close()


@router.get("/<request_id>")
def get_request(request_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        return jsonify(serialize_request(item))
    finally:
        db.close()


@router.patch("/<request_id>")
def patch_request(request_id: str):
    try:
        payload = RequestPatch.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        from .domain import location_visibility as visibility

        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        if payload.address is not None and visibility(db, item, user) != "DOMICILIO_AUTORIZADO":
            raise ApiError(400, "BAD_REQUEST", "El domicilio solo se acepta cuando RF-52 lo autoriza")
        if payload.description is not None:
            item.description = payload.description
        if payload.dimensions is not None:
            item.dimensions = payload.dimensions
        if payload.materials is not None:
            item.materials = payload.materials
        if payload.desired_date is not None:
            item.desired_date = payload.desired_date
        if payload.address is not None:
            item.address = payload.address
        if payload.summary_confirmed:
            missing = _ready_for_search(item)
            if missing:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "Faltan campos mínimos para confirmar",
                    [{"field": field, "message": "requerido"} for field in missing],
                )
            item.summary_confirmed = True
            item.status = ProjectStatus.CONFIRMADA
            item.confirmed_at = utcnow()
            append_audit(db, item, user.id, "SOLICITUD_CONFIRMADA")
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item))
    finally:
        db.close()


@router.post("/<request_id>/attachments")
def add_attachment(request_id: str):
    try:
        payload = FileUploadRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    if payload.size_bytes > 5_242_880:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "Archivo excede el límite")
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        stored = StoredFile(
            request_id=item.id,
            owner_id=user.id,
            file_type=FileType.VIDEO if payload.content_type == "video/mp4" else FileType.IMAGE,
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


@router.post("/<request_id>/visual-representations")
def create_visual(request_id: str):
    body = request.get_json(silent=True) or {}
    description = body.get("description")
    reference_ids = body.get("referenceFileIds") or []
    if not description or not reference_ids:
        raise ApiError(422, "VALIDATION_ERROR", "description y referenceFileIds son requeridos")
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        file_id = parse_uuid(str(reference_ids[0]), "referenceFileIds")
        stored = db.get(StoredFile, file_id)
        if stored is None or stored.request_id != item.id:
            raise ApiError(404, "NOT_FOUND", "Archivo de referencia no encontrado")
        visual = VisualRepresentation(
            request_id=item.id,
            description=description,
            reference_file_id=stored.id,
            status=VisualStatus.DISPONIBLE,
            is_technical_plan=False,
        )
        db.add(visual)
        db.commit()
        db.refresh(visual)
        return (
            jsonify(
                {
                    "id": str(visual.id),
                    "status": visual.status.value,
                    "description": visual.description,
                    "referenceFileId": str(visual.reference_file_id),
                    "isTechnicalPlan": False,
                }
            ),
            201,
        )
    finally:
        db.close()


def _search_providers(db: Session, item: ServiceRequest, payload: SearchRequest):
    rejected = {row.provider_id for row in item.rejections}
    matches = []
    for provider in db.scalars(select(Provider)).all():
        if not is_complete_provider(provider) or provider.id in rejected:
            continue
        trades = {row.trade for row in provider.trades}
        zones = {row.zone.lower() for row in provider.coverage}
        if item.trade and item.trade not in trades:
            continue
        if item.approximate_zone and item.approximate_zone.lower() not in zones:
            continue
        if item.desired_date and any(row.day == item.desired_date for row in provider.unavailable_dates):
            continue
        if payload.verified_only and not is_verified(provider):
            continue
        if payload.similar_experience and rating_summary(db, provider.id)["count"] == 0:
            continue
        price = float(provider.reference_price_mxn) if provider.reference_price_mxn is not None else None
        if payload.price_min is not None and (price is None or price < payload.price_min):
            if not payload.include_without_comparable_price or price is not None:
                continue
        if payload.price_max is not None and (price is None or price > payload.price_max):
            if not payload.include_without_comparable_price or price is not None:
                continue
        matches.append(provider)

    def sort_key(provider: Provider):
        rating = rating_summary(db, provider.id)["average"]
        nearby = 0 if item.approximate_zone and any(
            item.approximate_zone.lower() == row.zone.lower() for row in provider.coverage
        ) else 1
        price = float(provider.reference_price_mxn or 10**9)
        if payload.sort == "rating":
            return (-rating, nearby)
        if payload.sort == "price":
            return (price, -rating)
        if payload.sort == "availability":
            return (0 if provider.general_availability else 1, -rating)
        if payload.sort == "guarantee":
            return (-(provider.guarantee_months or 0), -rating)
        return (nearby, -rating)

    matches.sort(key=sort_key)
    return matches


@router.post("/<request_id>/search")
def search_providers(request_id: str):
    try:
        payload = SearchRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        missing = _ready_for_search(item)
        if missing:
            raise ApiError(
                422,
                "VALIDATION_ERROR",
                "Faltan campos mínimos para buscar",
                [{"field": field, "message": "requerido"} for field in missing],
            )
        matches = _search_providers(db, item, payload)
        recommendations = []
        for provider in matches[:4]:
            criteria = ["oficio", "zona aproximada"]
            if is_verified(provider):
                criteria.append("verificación")
            recommendations.append(
                {
                    "provider": serialize_provider(provider, db, user),
                    "explanation": "Coincidencia por oficio y cobertura, sin prometer resultado.",
                    "criteria": criteria,
                }
            )
        return jsonify(
            {
                "items": [serialize_provider(item, db, user) for item in matches],
                "recommendations": recommendations,
                "noResultsMessage": None
                if matches
                else "No encontramos proveedores con ese oficio y zona. Prueba ampliar filtros.",
                "page": page_info(1, max(len(matches), 1), len(matches)),
            }
        )
    finally:
        db.close()


@router.put("/<request_id>/selection")
def select_provider(request_id: str):
    body = request.get_json(silent=True) or {}
    if not body.get("providerId"):
        raise ApiError(422, "VALIDATION_ERROR", "providerId es requerido")
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        provider = db.get(Provider, parse_uuid(str(body["providerId"]), "providerId"))
        if provider is None:
            raise ApiError(404, "NOT_FOUND", "Proveedor no encontrado")
        item.selected_provider_id = provider.id
        item.decision_expires_at = utcnow().replace(hour=23, minute=59)
        append_audit(db, item, user.id, "PROVEEDOR_SELECCIONADO")
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item))
    finally:
        db.close()


@router.post("/<request_id>/provider-decision")
def provider_decision(request_id: str):
    body = request.get_json(silent=True) or {}
    decision = body.get("decision")
    if decision not in {"ACEPTAR", "RECHAZAR"}:
        raise ApiError(422, "VALIDATION_ERROR", "decisión inválida")
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        provider = provider_of(user, db)
        if provider is None or item.selected_provider_id != provider.id:
            raise ApiError(403, "FORBIDDEN", "Solo el proveedor seleccionado puede decidir")
        if item.decision_expires_at and item.decision_expires_at < utcnow():
            raise ApiError(409, "CONFLICT", "Solicitud expirada o ya decidida")
        if decision == "RECHAZAR":
            db.add(RequestRejection(request_id=item.id, provider_id=provider.id))
            item.selected_provider_id = None
            item.decision_expires_at = None
            append_audit(db, item, user.id, "PROVEEDOR_RECHAZO")
        else:
            append_audit(db, item, user.id, "PROVEEDOR_ACEPTO")
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item))
    finally:
        db.close()


@router.post("/<request_id>/support-requests")
def create_support(request_id: str):
    body = request.get_json(silent=True) or {}
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise ApiError(422, "VALIDATION_ERROR", "reason es requerido")
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_owner(user, item)
        case = SupportCase(request_id=item.id, reason=reason, status=SupportStatus.REGISTRADA)
        db.add(case)
        append_audit(db, item, user.id, "SOPORTE_SOLICITADO")
        db.commit()
        db.refresh(case)
        return (
            jsonify(
                {
                    "id": str(case.id),
                    "status": case.status.value,
                    "createdAt": case.created_at.isoformat(),
                }
            ),
            201,
        )
    finally:
        db.close()


@router.patch("/<request_id>/status")
def update_status(request_id: str):
    try:
        payload = StatusPatch.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    if user.role == UserRole.ADMINISTRADOR:
        raise ApiError(403, "FORBIDDEN", "El administrador no cambia el cierre comercial")
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        allowed = STATUS_TRANSITIONS.get(item.status.value, set())
        if payload.status.value not in allowed:
            raise ApiError(409, "CONFLICT", "Transición no permitida")
        if payload.status == ProjectStatus.EN_PROCESO and not has_accepted_proposal(db, item):
            raise ApiError(409, "CONFLICT", "No inicia trabajo sin propuesta aceptada")
        if payload.status == ProjectStatus.TERMINADO and user.role != UserRole.PROVEEDOR:
            raise ApiError(403, "FORBIDDEN", "Solo el proveedor marca terminado")
        if payload.status == ProjectStatus.CONCLUIDO and user.role != UserRole.CLIENTE:
            raise ApiError(403, "FORBIDDEN", "Solo el cliente confirma el cierre")
        if payload.status == ProjectStatus.EN_PROCESO and item.status == ProjectStatus.TERMINADO:
            if user.role != UserRole.CLIENTE:
                raise ApiError(403, "FORBIDDEN", "Solo el cliente puede rechazar el cierre")
            append_audit(db, item, user.id, f"CIERRE_RECHAZADO:{payload.reason or ''}")
        item.status = payload.status
        if payload.status == ProjectStatus.CONCLUIDO:
            item.concluded_at = utcnow()
        append_audit(db, item, user.id, f"ESTADO_{payload.status.value}")
        db.commit()
        db.refresh(item)
        return jsonify(serialize_request(item))
    finally:
        db.close()


@router.get("/<request_id>/messages")
def list_messages(request_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        messages = list(
            db.scalars(
                select(Message)
                .where(Message.request_id == item.id)
                .order_by(Message.sent_at.asc())
            )
        )
        return jsonify(
            {
                "items": [
                    {
                        "id": str(message.id),
                        "content": strip_phones(message.content),
                        "senderId": str(message.sender_id),
                        "sentAt": message.sent_at.isoformat(),
                    }
                    for message in messages
                ],
                "page": page_info(1, max(len(messages), 1), len(messages)),
            }
        )
    finally:
        db.close()


@router.post("/<request_id>/messages")
def create_message(request_id: str):
    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        raise ApiError(422, "VALIDATION_ERROR", "content es requerido")
    if contains_phone(content):
        raise ApiError(422, "VALIDATION_ERROR", "El canal no admite teléfonos")
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        has_appointment = db.scalar(
            select(Appointment).where(
                Appointment.request_id == item.id,
                Appointment.status.in_(
                    [AppointmentStatus.PENDIENTE, AppointmentStatus.CONFIRMADA]
                ),
            )
        )
        if has_appointment is None:
            raise ApiError(403, "FORBIDDEN", "El canal se habilita cuando hay una cita")
        message = Message(request_id=item.id, sender_id=user.id, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return (
            jsonify(
                {
                    "id": str(message.id),
                    "content": message.content,
                    "senderId": str(message.sender_id),
                    "sentAt": message.sent_at.isoformat(),
                }
            ),
            201,
        )
    finally:
        db.close()


@router.get("/<request_id>/audit-log")
def list_audit(request_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        events = list(
            db.scalars(
                select(AuditEvent)
                .where(AuditEvent.request_id == item.id)
                .order_by(AuditEvent.occurred_at.asc())
            )
        )
        return jsonify(
            {
                "items": [
                    {
                        "id": str(event.id),
                        "action": event.action,
                        "actorId": str(event.actor_id),
                        "occurredAt": event.occurred_at.isoformat(),
                        "previousEventId": str(event.previous_event_id)
                        if event.previous_event_id
                        else None,
                    }
                    for event in events
                ]
            }
        )
    finally:
        db.close()


@router.post("/<request_id>/evaluations")
def create_evaluation(request_id: str):
    try:
        payload = EvaluationCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        if item.status != ProjectStatus.CONCLUIDO:
            raise ApiError(403, "FORBIDDEN", "Solo se evalúa un proyecto concluido")
        if item.concluded_at:
            concluded = item.concluded_at
            if concluded.tzinfo is None:
                concluded = concluded.replace(tzinfo=timezone.utc)
            if utcnow() > concluded + timedelta(days=7):
                raise ApiError(409, "CONFLICT", "Evaluación duplicada o ventana cerrada")
        existing = db.scalar(
            select(Evaluation).where(
                Evaluation.request_id == item.id,
                Evaluation.author_id == user.id,
            )
        )
        if existing is not None:
            raise ApiError(409, "CONFLICT", "Evaluación duplicada o ventana cerrada")
        if payload.subject_type == "PROVEEDOR" and user.role != UserRole.CLIENTE:
            raise ApiError(403, "FORBIDDEN", "Solo el cliente evalúa al proveedor")
        if payload.subject_type == "CLIENTE" and user.role != UserRole.PROVEEDOR:
            raise ApiError(403, "FORBIDDEN", "Solo el proveedor evalúa al cliente")
        evaluation = Evaluation(
            request_id=item.id,
            author_id=user.id,
            provider_id=item.selected_provider_id,
            score=payload.score,
            punctuality=payload.punctuality,
            quality=payload.quality,
            cleanliness=payload.cleanliness,
            budget_adherence=payload.budget_adherence,
            comment=payload.comment,
            subject_type=EvaluationSubject(payload.subject_type),
            status=EvaluationStatus.PENDIENTE,
        )
        db.add(evaluation)
        db.flush()
        pending = list(
            db.scalars(
                select(Evaluation).where(
                    Evaluation.request_id == item.id,
                    Evaluation.status == EvaluationStatus.PENDIENTE,
                )
            )
        )
        if len(pending) >= 2:
            for row in pending:
                row.status = EvaluationStatus.PUBLICADA
        db.commit()
        db.refresh(evaluation)
        return (
            jsonify(
                {
                    "id": str(evaluation.id),
                    "subjectType": evaluation.subject_type.value,
                    "punctuality": evaluation.punctuality,
                    "quality": evaluation.quality,
                    "cleanliness": evaluation.cleanliness,
                    "budgetAdherence": evaluation.budget_adherence,
                    "score": evaluation.score,
                    "comment": evaluation.comment,
                    "status": evaluation.status.value,
                    "createdAt": evaluation.created_at.isoformat(),
                }
            ),
            201,
        )
    finally:
        db.close()


@router.get("/<request_id>/privacy")
def get_private_location(request_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        visibility = location_visibility(db, item, user)
        municipality = item.approximate_zone
        neighborhood = item.approximate_zone
        payload = {
            "visibility": visibility,
            "municipality": municipality,
            "neighborhood": neighborhood,
        }
        if visibility == "DOMICILIO_AUTORIZADO":
            payload["exactAddress"] = item.address
            payload["media"] = [serialize_file(file) for file in item.files]
        else:
            payload["exactAddress"] = None
            payload["media"] = []
        return jsonify(payload)
    finally:
        db.close()
