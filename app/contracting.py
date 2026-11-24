from datetime import timedelta

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import SessionLocal
from .domain import (
    append_audit,
    expire_pending_entities,
    get_request_or_404,
    has_accepted_proposal,
    parse_uuid,
    provider_of,
    require_owner,
    require_request_access,
    serialize_appointment,
    serialize_proposal,
    utcnow,
)
from .errors import ApiError, validation_error
from .models import (
    Appointment,
    AppointmentStatus,
    BudgetVersion,
    Change,
    ChangeStatus,
    ProjectStatus,
    Proposal,
    ProposalStatus,
    ServiceRequest,
    User,
    UserRole,
)
from .schemas import (
    AppointmentCreate,
    AppointmentPatch,
    CancelRequest,
    ChangeCreate,
    ChangeDecision,
    PageQuery,
    ProposalCreate,
    ProposalDecision,
    page_info,
)
from .security import get_current_user

appointments = Blueprint("appointments", __name__)
proposals = Blueprint("proposals", __name__)
changes = Blueprint("changes", __name__)


def _require_appointment_access(user: User, appointment: Appointment, db: Session) -> ServiceRequest:
    item = get_request_or_404(db, appointment.request_id)
    require_request_access(user, item, db)
    return item


def _accessible_request_ids(db: Session, user: User) -> list:
    if user.role == UserRole.ADMINISTRADOR:
        return list(db.scalars(select(ServiceRequest.id)))
    provider = provider_of(user, db) if user.role == UserRole.PROVEEDOR else None
    if provider is not None:
        return list(
            db.scalars(
                select(ServiceRequest.id).where(
                    (ServiceRequest.owner_id == user.id)
                    | (ServiceRequest.selected_provider_id == provider.id)
                )
            )
        )
    return list(db.scalars(select(ServiceRequest.id).where(ServiceRequest.owner_id == user.id)))


def _has_overlap(db: Session, provider_id, starts_at, ends_at, ignore_id=None) -> bool:
    rows = db.scalars(
        select(Appointment).where(
            Appointment.provider_id == provider_id,
            Appointment.status == AppointmentStatus.CONFIRMADA,
        )
    )
    for row in rows:
        if ignore_id and row.id == ignore_id:
            continue
        if starts_at < row.ends_at and ends_at > row.starts_at:
            return True
    return False


def _refresh_confirmation(appointment: Appointment, item: ServiceRequest, db: Session, actor_id) -> None:
    if appointment.confirmed_by_client and appointment.confirmed_by_provider:
        if _has_overlap(db, appointment.provider_id, appointment.starts_at, appointment.ends_at, appointment.id):
            raise ApiError(409, "CONFLICT", "Conflicto de horario")
        appointment.status = AppointmentStatus.CONFIRMADA
        if item.status in {ProjectStatus.CONFIRMADA, ProjectStatus.BORRADOR}:
            item.status = ProjectStatus.PROGRAMADO
        append_audit(db, item, actor_id, "CITA_CONFIRMADA")


@appointments.get("")
def list_appointments():
    user = get_current_user()
    pagination = PageQuery.model_validate(request.args.to_dict())
    request_id = request.args.get("requestId")
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        query = select(Appointment)
        if request_id:
            item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
            require_request_access(user, item, db)
            query = query.where(Appointment.request_id == item.id)
        else:
            accessible = _accessible_request_ids(db, user)
            if not accessible:
                return jsonify(
                    {
                        "items": [],
                        "page": page_info(pagination.page, pagination.page_size, 0),
                    }
                )
            query = query.where(Appointment.request_id.in_(accessible))
        rows = list(db.scalars(query.order_by(Appointment.starts_at.asc())))
        start = (pagination.page - 1) * pagination.page_size
        page_items = rows[start : start + pagination.page_size]
        return jsonify(
            {
                "items": [serialize_appointment(row) for row in page_items],
                "page": page_info(pagination.page, pagination.page_size, len(rows)),
            }
        )
    finally:
        db.close()


@appointments.post("")
def create_appointment():
    try:
        payload = AppointmentCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        item = get_request_or_404(db, payload.request_id)
        require_request_access(user, item, db)
        provider = provider_of(user, db) if user.role == UserRole.PROVEEDOR else None
        provider_id = item.selected_provider_id
        if provider_id is None:
            raise ApiError(409, "CONFLICT", "La solicitud no tiene proveedor asociado")
        if user.role == UserRole.PROVEEDOR and (provider is None or provider.id != provider_id):
            raise ApiError(403, "FORBIDDEN", "Solo el proveedor asociado propone la cita")
        if not payload.is_visit and not has_accepted_proposal(db, item):
            raise ApiError(409, "CONFLICT", "La cita de ejecución exige propuesta aceptada")
        if _has_overlap(db, provider_id, payload.starts_at, payload.ends_at):
            raise ApiError(409, "CONFLICT", "Franjas no disponibles")
        appointment = Appointment(
            request_id=item.id,
            provider_id=provider_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            cost_mxn=payload.cost_mxn,
            is_visit=True if payload.is_visit is None else payload.is_visit,
            confirmed_by_provider=payload.confirmed_by_provider,
            confirmed_by_client=user.role == UserRole.CLIENTE,
            status=AppointmentStatus.PENDIENTE,
            expires_at=utcnow() + timedelta(hours=24),
        )
        db.add(appointment)
        db.flush()
        append_audit(db, item, user.id, "CITA_PROPUESTA")
        _refresh_confirmation(appointment, item, db, user.id)
        db.commit()
        db.refresh(appointment)
        return jsonify(serialize_appointment(appointment)), 201
    finally:
        db.close()


@appointments.get("/<appointment_id>")
def get_appointment(appointment_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        appointment = db.get(Appointment, parse_uuid(appointment_id, "appointmentId"))
        if appointment is None:
            raise ApiError(404, "NOT_FOUND", "Cita no encontrada")
        _require_appointment_access(user, appointment, db)
        return jsonify(serialize_appointment(appointment))
    finally:
        db.close()


@appointments.patch("/<appointment_id>")
def update_appointment(appointment_id: str):
    try:
        payload = AppointmentPatch.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        appointment = db.get(Appointment, parse_uuid(appointment_id, "appointmentId"))
        if appointment is None:
            raise ApiError(404, "NOT_FOUND", "Cita no encontrada")
        item = _require_appointment_access(user, appointment, db)
        if payload.starts_at is not None:
            appointment.starts_at = payload.starts_at
        if payload.ends_at is not None:
            appointment.ends_at = payload.ends_at
        if payload.confirmed_by_client is not None:
            if user.role != UserRole.CLIENTE:
                raise ApiError(403, "FORBIDDEN", "Solo el cliente confirma su lado")
            appointment.confirmed_by_client = payload.confirmed_by_client
        if payload.confirmed_by_provider is not None:
            if user.role != UserRole.PROVEEDOR:
                raise ApiError(403, "FORBIDDEN", "Solo el proveedor confirma su lado")
            appointment.confirmed_by_provider = payload.confirmed_by_provider
        _refresh_confirmation(appointment, item, db, user.id)
        append_audit(db, item, user.id, "CITA_ACTUALIZADA")
        db.commit()
        db.refresh(appointment)
        return jsonify(serialize_appointment(appointment))
    finally:
        db.close()


@appointments.delete("/<appointment_id>")
def cancel_appointment(appointment_id: str):
    try:
        payload = CancelRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        appointment = db.get(Appointment, parse_uuid(appointment_id, "appointmentId"))
        if appointment is None:
            raise ApiError(404, "NOT_FOUND", "Cita no encontrada")
        item = _require_appointment_access(user, appointment, db)
        appointment.status = AppointmentStatus.CANCELADA
        appointment.cancel_reason = payload.reason
        append_audit(db, item, user.id, f"CITA_CANCELADA:{payload.reason}")
        db.commit()
        db.refresh(appointment)
        return jsonify(serialize_appointment(appointment))
    finally:
        db.close()


@proposals.get("")
def list_proposals():
    user = get_current_user()
    pagination = PageQuery.model_validate(request.args.to_dict())
    request_id = request.args.get("requestId")
    if not request_id:
        raise ApiError(422, "VALIDATION_ERROR", "requestId es requerido")
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        item = get_request_or_404(db, parse_uuid(request_id, "requestId"))
        require_request_access(user, item, db)
        rows = list(
            db.scalars(
                select(Proposal)
                .where(Proposal.request_id == item.id)
                .order_by(Proposal.version.desc())
            )
        )
        start = (pagination.page - 1) * pagination.page_size
        page_items = rows[start : start + pagination.page_size]
        return jsonify(
            {
                "items": [serialize_proposal(row) for row in page_items],
                "page": page_info(pagination.page, pagination.page_size, len(rows)),
            }
        )
    finally:
        db.close()


@proposals.post("")
def create_proposal():
    try:
        payload = ProposalCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, payload.request_id)
        provider = provider_of(user, db)
        if provider is None or item.selected_provider_id != provider.id:
            raise ApiError(403, "FORBIDDEN", "Solo el proveedor asociado envía propuesta")
        previous = list(db.scalars(select(Proposal).where(Proposal.request_id == item.id)))
        first = min((row.issued_at for row in previous), default=utcnow())
        proposal = Proposal(
            request_id=item.id,
            provider_id=provider.id,
            version=len(previous) + 1,
            status=ProposalStatus.ENVIADA,
            work_description=payload.work_description,
            total_mxn=payload.total_mxn,
            labor_subtotal_mxn=payload.labor_subtotal_mxn,
            additional_costs_mxn=payload.additional_costs_mxn,
            dates=[day.isoformat() for day in payload.dates],
            materials=[item.model_dump(by_alias=True) for item in payload.materials],
            issued_at=utcnow(),
            expires_at=first + timedelta(days=5),
        )
        db.add(proposal)
        db.flush()
        append_audit(db, item, user.id, "PROPUESTA_ENVIADA")
        db.commit()
        db.refresh(proposal)
        return jsonify(serialize_proposal(proposal)), 201
    finally:
        db.close()


@proposals.post("/<proposal_id>/decision")
def decide_proposal(proposal_id: str):
    try:
        payload = ProposalDecision.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        proposal = db.get(Proposal, parse_uuid(proposal_id, "proposalId"))
        if proposal is None:
            raise ApiError(404, "NOT_FOUND", "Propuesta no encontrada")
        item = get_request_or_404(db, proposal.request_id)
        require_owner(user, item)
        if proposal.status != ProposalStatus.ENVIADA:
            raise ApiError(409, "CONFLICT", "Estado incompatible")
        if payload.decision == "ACEPTAR":
            proposal.status = ProposalStatus.ACEPTADA
            db.add(
                BudgetVersion(
                    proposal_id=proposal.id,
                    number=1,
                    total_mxn=proposal.total_mxn,
                    difference_from_initial_mxn=0,
                )
            )
            append_audit(db, item, user.id, "PROPUESTA_ACEPTADA")
        elif payload.decision == "PEDIR_CAMBIOS":
            proposal.status = ProposalStatus.NEGOCIACION
            append_audit(db, item, user.id, "PROPUESTA_AJUSTE")
        else:
            proposal.status = ProposalStatus.RECHAZADA
            append_audit(db, item, user.id, "PROPUESTA_RECHAZADA")
        db.commit()
        db.refresh(proposal)
        return jsonify(serialize_proposal(proposal))
    finally:
        db.close()


def _serialize_change(change: Change) -> dict:
    return {
        "id": str(change.id),
        "requestId": str(change.request_id),
        "type": change.change_type,
        "reason": change.reason,
        "amountDeltaMxn": float(change.amount_delta_mxn),
        "updatedTotalMxn": float(change.updated_total_mxn),
        "affectedItems": change.affected_items or [],
        "proposedDate": change.proposed_date.isoformat() if change.proposed_date else None,
        "initiatedBy": change.initiated_by,
        "status": change.status.value,
        "createdAt": change.created_at.isoformat(),
        "expiresAt": change.expires_at.isoformat(),
        "aiAnalysis": change.ai_analysis,
    }


@changes.post("")
def create_change():
    try:
        payload = ChangeCreate.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        item = get_request_or_404(db, payload.request_id)
        require_request_access(user, item, db)
        change = Change(
            request_id=item.id,
            initiated_by_id=user.id,
            change_type=payload.type,
            reason=payload.reason,
            amount_delta_mxn=payload.amount_delta_mxn,
            updated_total_mxn=payload.updated_total_mxn,
            affected_items=payload.affected_items,
            proposed_date=payload.proposed_date,
            initiated_by=payload.initiated_by or user.role.value,
            expires_at=utcnow() + timedelta(hours=48),
        )
        db.add(change)
        db.flush()
        append_audit(db, item, user.id, "CAMBIO_PENDIENTE")
        db.commit()
        db.refresh(change)
        return jsonify(_serialize_change(change)), 201
    finally:
        db.close()


@changes.patch("/<change_id>/decision")
def decide_change(change_id: str):
    try:
        payload = ChangeDecision.model_validate(request.get_json(silent=True) or {})
    except ValidationError as error:
        return validation_error(error)
    user = get_current_user()
    db = SessionLocal()
    try:
        expire_pending_entities(db)
        change = db.get(Change, parse_uuid(change_id, "changeId"))
        if change is None:
            raise ApiError(404, "NOT_FOUND", "Cambio no encontrado")
        item = get_request_or_404(db, change.request_id)
        require_request_access(user, item, db)
        if change.status != ChangeStatus.PENDIENTE:
            raise ApiError(409, "CONFLICT", "Cambio vencido o estado incompatible")
        if change.initiated_by_id == user.id and payload.decision != "CONTRAPROPONER":
            raise ApiError(403, "FORBIDDEN", "La contraparte debe decidir el cambio")
        if payload.decision == "ACEPTAR":
            change.status = ChangeStatus.ACEPTADO
            accepted = db.scalar(
                select(Proposal).where(
                    Proposal.request_id == item.id,
                    Proposal.status == ProposalStatus.ACEPTADA,
                )
            )
            if accepted is not None:
                versions = list(accepted.budget_versions)
                db.add(
                    BudgetVersion(
                        proposal_id=accepted.id,
                        number=len(versions) + 1,
                        total_mxn=change.updated_total_mxn,
                        difference_from_initial_mxn=change.amount_delta_mxn,
                    )
                )
            append_audit(db, item, user.id, "CAMBIO_ACEPTADO")
        elif payload.decision == "RECHAZAR":
            change.status = ChangeStatus.RECHAZADO
            append_audit(db, item, user.id, "CAMBIO_RECHAZADO")
        else:
            if payload.updated_terms is None:
                raise ApiError(422, "VALIDATION_ERROR", "updatedTerms es requerido")
            change.status = ChangeStatus.NO_ACEPTADO
            counter = Change(
                request_id=item.id,
                initiated_by_id=user.id,
                change_type=payload.updated_terms.type,
                reason=payload.updated_terms.reason,
                amount_delta_mxn=payload.updated_terms.amount_delta_mxn,
                updated_total_mxn=payload.updated_terms.updated_total_mxn,
                affected_items=payload.updated_terms.affected_items,
                proposed_date=payload.updated_terms.proposed_date,
                initiated_by=user.role.value,
                expires_at=utcnow() + timedelta(hours=48),
            )
            db.add(counter)
            append_audit(db, item, user.id, "CAMBIO_CONTRAPROPUESTA")
        db.commit()
        db.refresh(change)
        return jsonify(_serialize_change(change))
    finally:
        db.close()


@changes.post("/<change_id>/analysis")
def analyze_change(change_id: str):
    user = get_current_user()
    db = SessionLocal()
    try:
        change = db.get(Change, parse_uuid(change_id, "changeId"))
        if change is None:
            raise ApiError(404, "NOT_FOUND", "Cambio no encontrado")
        item = get_request_or_404(db, change.request_id)
        require_request_access(user, item, db)
        missing = []
        if not change.affected_items:
            missing.append("affectedItems")
        summary = (
            f"El cambio de tipo {change.change_type} ajusta {change.amount_delta_mxn} MXN. "
            "Este análisis es informativo y no decide por las partes."
        )
        change.ai_analysis = summary
        db.commit()
        return jsonify(
            {
                "summary": summary,
                "missingData": missing,
                "risks": ["El presupuesto vigente no cambia hasta que una parte acepte."],
                "isDecision": False,
            }
        )
    finally:
        db.close()
