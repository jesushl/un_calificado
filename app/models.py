from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, Enum):
    CLIENTE = "CLIENTE"
    PROVEEDOR = "PROVEEDOR"
    ADMINISTRADOR = "ADMINISTRADOR"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.CLIENTE)
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(UserStatus), default=UserStatus.ACTIVE
    )
    privacy_consent_version: Mapped[str] = mapped_column(String(80))
    adult_declaration: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    provider: Mapped["Provider | None"] = relationship(back_populates="account")
    requests: Mapped[list["ServiceRequest"]] = relationship(
        back_populates="owner", foreign_keys="ServiceRequest.owner_id"
    )
    consents: Mapped[list["Consent"]] = relationship(back_populates="user")


class ProviderModality(str, Enum):
    TRABAJADOR = "TRABAJADOR"
    ORGANIZACION = "ORGANIZACION"


class ProjectStatus(str, Enum):
    BORRADOR = "BORRADOR"
    CONFIRMADA = "CONFIRMADA"
    PROGRAMADO = "PROGRAMADO"
    EN_PROCESO = "EN_PROCESO"
    TERMINADO = "TERMINADO"
    CONCLUIDO = "CONCLUIDO"


class AppointmentStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    EXPIRADA = "EXPIRADA"
    CANCELADA = "CANCELADA"


class ProposalStatus(str, Enum):
    ENVIADA = "ENVIADA"
    ACEPTADA = "ACEPTADA"
    NEGOCIACION = "NEGOCIACION"
    RECHAZADA = "RECHAZADA"
    EXPIRADA = "EXPIRADA"


class ChangeStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADO = "ACEPTADO"
    RECHAZADO = "RECHAZADO"
    NO_ACEPTADO = "NO_ACEPTADO"
    EXPIRADO = "EXPIRADO"


class VerificationStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    VERIFICADA = "VERIFICADA"
    RECHAZADA = "RECHAZADA"
    RETIRADA = "RETIRADA"


class EvaluationStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    PUBLICADA = "PUBLICADA"
    VENCIDA = "VENCIDA"


class FileType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    modality: Mapped[ProviderModality] = mapped_column(SqlEnum(ProviderModality))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    general_availability: Mapped[str | None] = mapped_column(String(255))
    account: Mapped[User] = relationship(back_populates="provider")
    trades: Mapped[list["ProviderTrade"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    coverage: Mapped[list["ProviderCoverage"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    availability: Mapped["Availability | None"] = relationship(
        back_populates="provider", cascade="all, delete-orphan", uselist=False
    )
    verifications: Mapped[list["Verification"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )


class ProviderTrade(Base):
    __tablename__ = "provider_trades"

    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), primary_key=True
    )
    trade: Mapped[str] = mapped_column(String(80), primary_key=True)
    provider: Mapped[Provider] = relationship(back_populates="trades")


class ProviderCoverage(Base):
    __tablename__ = "provider_coverage"

    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), primary_key=True
    )
    zone: Mapped[str] = mapped_column(String(160), primary_key=True)
    provider: Mapped[Provider] = relationship(back_populates="coverage")


class Availability(Base):
    __tablename__ = "availabilities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), unique=True
    )
    general_status: Mapped[str] = mapped_column(String(40), default="DECLARADA")
    provider: Mapped[Provider] = relationship(back_populates="availability")
    slots: Mapped[list["AvailabilitySlot"]] = relationship(
        back_populates="availability", cascade="all, delete-orphan"
    )


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    availability_id: Mapped[UUID] = mapped_column(
        ForeignKey("availabilities.id", ondelete="CASCADE")
    )
    weekday: Mapped[int] = mapped_column(Integer)
    starts_at: Mapped[str] = mapped_column(String(5))
    ends_at: Mapped[str] = mapped_column(String(5))
    availability: Mapped[Availability] = relationship(back_populates="slots")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    selected_provider_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("providers.id", ondelete="SET NULL")
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SqlEnum(ProjectStatus), default=ProjectStatus.BORRADOR
    )
    expected_outcome: Mapped[str] = mapped_column(Text)
    trade: Mapped[str | None] = mapped_column(String(80))
    approximate_zone: Mapped[str] = mapped_column(String(160))
    desired_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    owner: Mapped[User] = relationship(
        back_populates="requests", foreign_keys=[owner_id]
    )
    selected_provider: Mapped["Provider | None"] = relationship(
        foreign_keys=[selected_provider_id]
    )
    files: Mapped[list["StoredFile"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    proposals: Mapped[list["Proposal"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    changes: Mapped[list["Change"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class StoredFile(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    provider_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE")
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    file_type: Mapped[FileType] = mapped_column(SqlEnum(FileType))
    file_name: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(500), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    request: Mapped["ServiceRequest | None"] = relationship(back_populates="files")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"))
    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(AppointmentStatus), default=AppointmentStatus.PENDIENTE
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cost_mxn: Mapped[float] = mapped_column(Numeric(12, 2))
    is_visit: Mapped[bool] = mapped_column(Boolean, default=True)
    request: Mapped[ServiceRequest] = relationship(back_populates="appointments")


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[ProposalStatus] = mapped_column(
        SqlEnum(ProposalStatus), default=ProposalStatus.ENVIADA
    )
    work_description: Mapped[str] = mapped_column(Text)
    total_mxn: Mapped[float] = mapped_column(Numeric(12, 2))
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request: Mapped[ServiceRequest] = relationship(back_populates="proposals")
    budget_versions: Mapped[list["BudgetVersion"]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan"
    )


class BudgetVersion(Base):
    __tablename__ = "budget_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    proposal_id: Mapped[UUID] = mapped_column(
        ForeignKey("proposals.id", ondelete="CASCADE")
    )
    number: Mapped[int] = mapped_column(Integer)
    total_mxn: Mapped[float] = mapped_column(Numeric(12, 2))
    difference_from_initial_mxn: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    proposal: Mapped[Proposal] = relationship(back_populates="budget_versions")


class Change(Base):
    __tablename__ = "changes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    initiated_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    change_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[ChangeStatus] = mapped_column(
        SqlEnum(ChangeStatus), default=ChangeStatus.PENDIENTE
    )
    reason: Mapped[str] = mapped_column(Text)
    amount_delta_mxn: Mapped[float] = mapped_column(Numeric(12, 2))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request: Mapped[ServiceRequest] = relationship(back_populates="changes")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    request: Mapped[ServiceRequest] = relationship(back_populates="messages")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[UUID] = mapped_column(ForeignKey("providers.id"))
    score: Mapped[int] = mapped_column(Integer)
    punctuality: Mapped[int | None] = mapped_column(Integer)
    quality: Mapped[int | None] = mapped_column(Integer)
    cleanliness: Mapped[int | None] = mapped_column(Integer)
    budget_adherence: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EvaluationStatus] = mapped_column(
        SqlEnum(EvaluationStatus), default=EvaluationStatus.PUBLICADA
    )
    request: Mapped[ServiceRequest] = relationship(back_populates="evaluations")


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE")
    )
    verification_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[VerificationStatus] = mapped_column(
        SqlEnum(VerificationStatus), default=VerificationStatus.PENDIENTE
    )
    reason: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider: Mapped[Provider] = relationship(back_populates="verifications")


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    privacy_version: Mapped[str] = mapped_column(String(80))
    adult_declaration: Mapped[bool] = mapped_column(Boolean)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    user: Mapped[User] = relationship(back_populates="consents")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE")
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    previous_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("audit_events.id")
    )
    request: Mapped[ServiceRequest] = relationship(back_populates="audit_events")
