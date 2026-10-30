from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .catalog import PHONE_PATTERN
from .errors import ApiError
from .models import (
    Appointment,
    AppointmentStatus,
    AuditEvent,
    Evaluation,
    EvaluationStatus,
    ProjectStatus,
    Proposal,
    ProposalStatus,
    Provider,
    ServiceRequest,
    StoredFile,
    User,
    UserRole,
    VerificationStatus,
)
from .storage import signed_download


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_uuid(value: str, name: str = "id") -> UUID:
    try:
        return UUID(value)
    except ValueError as error:
        raise ApiError(400, "BAD_REQUEST", f"{name} inválido") from error


def append_audit(db: Session, request: ServiceRequest, actor_id: UUID, action: str) -> AuditEvent:
    previous = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.request_id == request.id)
        .order_by(AuditEvent.occurred_at.desc())
    ).first()
    event = AuditEvent(
        request_id=request.id,
        actor_id=actor_id,
        action=action,
        previous_event_id=previous.id if previous else None,
    )
    db.add(event)
    request.updated_at = utcnow()
    return event


def provider_of(user: User, db: Session) -> Provider | None:
    return db.scalar(select(Provider).where(Provider.account_id == user.id))


def get_request_or_404(db: Session, request_id: UUID) -> ServiceRequest:
    request = db.get(ServiceRequest, request_id)
    if request is None:
        raise ApiError(404, "NOT_FOUND", "Solicitud no encontrada")
    return request


def is_request_participant(user: User, request: ServiceRequest, db: Session) -> bool:
    if user.role == UserRole.ADMINISTRADOR:
        return True
    if request.owner_id == user.id:
        return True
    provider = provider_of(user, db)
    return provider is not None and request.selected_provider_id == provider.id


def require_request_access(user: User, request: ServiceRequest, db: Session) -> None:
    if not is_request_participant(user, request, db):
        raise ApiError(403, "FORBIDDEN", "El rol no tiene permiso para esta ruta")


def require_owner(user: User, request: ServiceRequest) -> None:
    if request.owner_id != user.id:
        raise ApiError(403, "FORBIDDEN", "Solo el cliente dueño puede hacer esta operación")


def has_accepted_proposal(db: Session, request: ServiceRequest) -> bool:
    return (
        db.scalar(
            select(Proposal).where(
                Proposal.request_id == request.id,
                Proposal.status == ProposalStatus.ACEPTADA,
            )
        )
        is not None
    )


def has_confirmed_visit(db: Session, request: ServiceRequest) -> bool:
    return (
        db.scalar(
            select(Appointment).where(
                Appointment.request_id == request.id,
                Appointment.status == AppointmentStatus.CONFIRMADA,
                Appointment.is_visit.is_(True),
            )
        )
        is not None
    )


def address_authorized_at(db: Session, request: ServiceRequest) -> datetime | None:
    moments = []
    proposal = db.scalar(
        select(Proposal)
        .where(
            Proposal.request_id == request.id,
            Proposal.status == ProposalStatus.ACEPTADA,
        )
        .order_by(Proposal.issued_at.asc())
    )
    if proposal is not None:
        moments.append(proposal.issued_at)
    visit = db.scalar(
        select(Appointment)
        .where(
            Appointment.request_id == request.id,
            Appointment.status == AppointmentStatus.CONFIRMADA,
            Appointment.is_visit.is_(True),
        )
        .order_by(Appointment.starts_at.asc())
    )
    if visit is not None:
        moments.append(visit.starts_at)
    if not moments:
        return None
    return min(moments)


def location_visibility(db: Session, request: ServiceRequest, viewer: User) -> str:
    provider = provider_of(viewer, db)
    if viewer.role == UserRole.PROVEEDOR and (
        provider is None or request.selected_provider_id != provider.id
    ):
        return "OCULTO"
    authorized_at = address_authorized_at(db, request)
    if authorized_at is None:
        return "ZONA_APROXIMADA"
    if utcnow() > authorized_at + timedelta(days=7):
        return "OCULTO"
    return "DOMICILIO_AUTORIZADO"


def can_show_provider_address(db: Session, provider: Provider, viewer: User) -> bool:
    if provider.modality.value != "TRABAJADOR":
        return False
    verified = any(
        item.status == VerificationStatus.VERIFICADA for item in provider.verifications
    )
    if not verified:
        return False
    appointment = db.scalar(
        select(Appointment)
        .join(ServiceRequest, Appointment.request_id == ServiceRequest.id)
        .where(
            Appointment.provider_id == provider.id,
            Appointment.status == AppointmentStatus.CONFIRMADA,
            ServiceRequest.owner_id == viewer.id,
        )
    )
    return appointment is not None


def is_complete_provider(provider: Provider) -> bool:
    return bool(provider.name and provider.trades and provider.coverage)


def is_verified(provider: Provider) -> bool:
    return any(item.status == VerificationStatus.VERIFICADA for item in provider.verifications)


def rating_summary(db: Session, provider_id: UUID) -> dict:
    rows = db.scalars(
        select(Evaluation).where(
            Evaluation.provider_id == provider_id,
            Evaluation.status == EvaluationStatus.PUBLICADA,
        )
    ).all()
    if not rows:
        return {"average": 0, "count": 0, "dimensions": {}}
    dimensions = {}
    for field in ("punctuality", "quality", "cleanliness", "budget_adherence"):
        values = [getattr(row, field) for row in rows if getattr(row, field) is not None]
        if values:
            dimensions[field] = round(sum(values) / len(values), 2)
    return {
        "average": round(sum(row.score for row in rows) / len(rows), 2),
        "count": len(rows),
        "dimensions": dimensions,
    }


def verification_map(provider: Provider) -> dict[str, str]:
    mapping = {"IDENTIDAD": "DECLARADA", "EXPERIENCIA": "DECLARADA", "ORGANIZACION": "DECLARADA"}
    for item in provider.verifications:
        mapping[item.verification_type] = item.status.value
    return mapping


def serialize_provider(
    provider: Provider,
    db: Session,
    viewer: User | None = None,
) -> dict:
    payload = {
        "id": str(provider.id),
        "name": provider.name,
        "modality": provider.modality.value,
        "trades": [item.trade for item in provider.trades],
        "experienceYears": provider.experience_years,
        "coverage": [item.zone for item in provider.coverage],
        "generalAvailability": provider.general_availability,
        "verificationStatus": verification_map(provider),
        "rating": rating_summary(db, provider.id),
        "updatedAt": provider.updated_at.isoformat() if provider.updated_at else utcnow().isoformat(),
    }
    if viewer is not None and can_show_provider_address(db, provider, viewer):
        payload["address"] = provider.address
    return payload


def serialize_request(request: ServiceRequest) -> dict:
    return {
        "id": str(request.id),
        "expectedOutcome": request.expected_outcome,
        "trade": request.trade,
        "approximateZone": request.approximate_zone,
        "desiredDate": request.desired_date.isoformat() if request.desired_date else None,
        "description": request.description,
        "aiConversationId": str(request.ai_conversation_id)
        if request.ai_conversation_id
        else None,
        "manualCapture": request.manual_capture,
        "status": request.status.value,
        "selectedProviderId": str(request.selected_provider_id)
        if request.selected_provider_id
        else None,
        "createdAt": request.created_at.isoformat(),
        "updatedAt": request.updated_at.isoformat() if request.updated_at else request.created_at.isoformat(),
    }


def serialize_file(file: StoredFile) -> dict:
    signed = signed_download(file.object_key, str(file.id))
    return {
        "id": str(file.id),
        "fileName": file.file_name,
        "contentType": file.mime_type,
        "sizeBytes": file.size_bytes,
        **signed,
    }


def serialize_appointment(appointment: Appointment) -> dict:
    return {
        "id": str(appointment.id),
        "requestId": str(appointment.request_id),
        "startsAt": appointment.starts_at.isoformat(),
        "endsAt": appointment.ends_at.isoformat(),
        "costMxn": float(appointment.cost_mxn),
        "confirmedByProvider": appointment.confirmed_by_provider,
        "isVisit": appointment.is_visit,
        "status": appointment.status.value,
        "expiresAt": appointment.expires_at.isoformat()
        if appointment.expires_at
        else None,
    }


def serialize_proposal(proposal: Proposal) -> dict:
    return {
        "id": str(proposal.id),
        "requestId": str(proposal.request_id),
        "workDescription": proposal.work_description,
        "dates": proposal.dates or [],
        "laborSubtotalMxn": float(proposal.labor_subtotal_mxn or 0),
        "materials": proposal.materials or [],
        "additionalCostsMxn": float(proposal.additional_costs_mxn or 0),
        "totalMxn": float(proposal.total_mxn),
        "version": proposal.version,
        "status": proposal.status.value,
        "issuedAt": proposal.issued_at.isoformat(),
        "expiresAt": proposal.expires_at.isoformat(),
    }


def contains_phone(text: str) -> bool:
    return bool(re.search(PHONE_PATTERN, text or ""))


def strip_phones(text: str) -> str:
    return re.sub(PHONE_PATTERN, "[teléfono omitido]", text or "")


def expire_pending_entities(db: Session) -> None:
    now = utcnow()
    for appointment in db.scalars(
        select(Appointment).where(
            Appointment.status == AppointmentStatus.PENDIENTE,
            Appointment.expires_at.is_not(None),
            Appointment.expires_at < now,
        )
    ):
        appointment.status = AppointmentStatus.EXPIRADA
    for proposal in db.scalars(
        select(Proposal).where(
            Proposal.status == ProposalStatus.ENVIADA,
            Proposal.expires_at < now,
        )
    ):
        proposal.status = ProposalStatus.EXPIRADA
    from .models import Change, ChangeStatus

    for change in db.scalars(
        select(Change).where(
            Change.status == ChangeStatus.PENDIENTE,
            Change.expires_at < now,
        )
    ):
        change.status = ChangeStatus.EXPIRADO
    for evaluation in db.scalars(select(Evaluation).where(Evaluation.status == EvaluationStatus.PENDIENTE)):
        request = db.get(ServiceRequest, evaluation.request_id)
        if request and request.concluded_at and now > request.concluded_at + timedelta(days=7):
            evaluation.status = EvaluationStatus.VENCIDA
    for request in db.scalars(
        select(ServiceRequest).where(
            ServiceRequest.decision_expires_at.is_not(None),
            ServiceRequest.decision_expires_at < now,
            ServiceRequest.status == ProjectStatus.CONFIRMADA,
        )
    ):
        request.selected_provider_id = None
        request.decision_expires_at = None
    db.flush()
