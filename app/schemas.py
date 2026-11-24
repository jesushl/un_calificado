from datetime import date, datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from .catalog import ALLOWED_TRADES
from .models import (
    PrivacyType,
    ProjectStatus,
    UserRole,
    UserStatus,
)

_MX_TZ = ZoneInfo("America/Mexico_City")


def _today_mexico() -> date:
    return datetime.now(_MX_TZ).date()


def _reject_past_desired_date(value: date | None) -> date | None:
    if value is not None and value < _today_mexico():
        raise ValueError("la fecha deseada debe ser hoy o una fecha futura")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    role: UserRole = UserRole.CLIENTE
    privacy_consent_version: str = Field(min_length=1, max_length=80)
    adult_declaration: bool

    @model_validator(mode="after")
    def validate_public_role(self):
        if self.role == UserRole.ADMINISTRADOR:
            raise ValueError("El rol administrador se aprovisiona internamente")
        if not self.adult_declaration:
            raise ValueError("Se requiere declarar mayoría de edad")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    status: UserStatus
    privacy_consent_version: str
    created_at: datetime
    name: str | None = None
    phone: str | None = None
    search_zone: str | None = None
    max_distance_km: int = 15


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class ConsentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    privacy_version: str = Field(alias="privacyVersion", min_length=1)
    adult_declaration: bool = Field(alias="adultDeclaration")

    @model_validator(mode="after")
    def require_adult(self):
        if not self.adult_declaration:
            raise ValueError("Se requiere declarar mayoría de edad")
        return self


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=160)
    phone: str | None = None
    search_zone: str | None = Field(default=None, alias="searchZone", max_length=160)
    max_distance_km: int | None = Field(default=None, alias="maxDistanceKm", ge=2, le=50)

    @model_validator(mode="after")
    def require_one_field(self):
        if (
            self.name is None
            and self.phone is None
            and self.search_zone is None
            and self.max_distance_km is None
        ):
            raise ValueError("Se requiere al menos un campo")
        return self


class ProviderUpsertRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=160)
    modality: str
    trades: list[str] = Field(min_length=1)
    experience_years: int = Field(alias="experienceYears", ge=0)
    coverage: list[str] = Field(min_length=1)
    general_availability: str | None = Field(default=None, alias="generalAvailability")
    address: str | None = None
    reference_price_mxn: float | None = Field(default=None, alias="referencePriceMxn", ge=0)
    guarantee_months: int | None = Field(default=None, alias="guaranteeMonths", ge=0)
    unavailable_dates: list[date] = Field(default_factory=list, alias="unavailableDates")

    @field_validator("modality")
    @classmethod
    def validate_modality(cls, value: str) -> str:
        if value not in {"TRABAJADOR", "ORGANIZACION"}:
            raise ValueError("modalidad inválida")
        return value

    @field_validator("trades")
    @classmethod
    def validate_trades(cls, value: list[str]) -> list[str]:
        invalid = [item for item in value if item not in ALLOWED_TRADES]
        if invalid:
            raise ValueError("oficio fuera del catálogo")
        return value


class RequestCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    expected_outcome: str = Field(alias="expectedOutcome", min_length=1)
    trade: str
    approximate_zone: str = Field(alias="approximateZone", min_length=1)
    desired_date: date | None = Field(default=None, alias="desiredDate")
    description: str | None = None
    ai_conversation_id: UUID | None = Field(default=None, alias="aiConversationId")
    manual_capture: bool = Field(default=False, alias="manualCapture")

    @field_validator("trade")
    @classmethod
    def validate_trade(cls, value: str) -> str:
        if value and value not in ALLOWED_TRADES:
            raise ValueError("oficio vacío o del catálogo")
        return value

    @field_validator("desired_date")
    @classmethod
    def validate_desired_date(cls, value: date | None) -> date | None:
        return _reject_past_desired_date(value)


class RequestPatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str | None = None
    dimensions: str | None = None
    materials: str | None = None
    summary_confirmed: bool | None = Field(default=None, alias="summaryConfirmed")
    desired_date: date | None = Field(default=None, alias="desiredDate")
    address: str | None = None

    @field_validator("desired_date")
    @classmethod
    def validate_desired_date(cls, value: date | None) -> date | None:
        return _reject_past_desired_date(value)

    @model_validator(mode="after")
    def require_one_field(self):
        if all(
            value is None
            for value in (
                self.description,
                self.dimensions,
                self.materials,
                self.summary_confirmed,
                self.desired_date,
                self.address,
            )
        ):
            raise ValueError("Se requiere al menos un campo")
        return self


class SearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    verified_only: bool | None = Field(default=None, alias="verifiedOnly")
    similar_experience: bool | None = Field(default=None, alias="similarExperience")
    sort: str | None = None
    price_min: float | None = Field(default=None, alias="priceMin", ge=0)
    price_max: float | None = Field(default=None, alias="priceMax", ge=0)
    include_without_comparable_price: bool = Field(
        default=False, alias="includeWithoutComparablePrice"
    )


class FileUploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_name: str = Field(alias="fileName")
    content_type: str = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes", ge=1, le=5_242_880)
    object_key: str = Field(alias="objectKey")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        if value not in {"image/jpeg", "image/png", "video/mp4"}:
            raise ValueError("formato no permitido; usa JPEG, PNG o MP4")
        return value


class VerificationRequest(BaseModel):
    type: str
    fileId: UUID

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"IDENTIDAD", "EXPERIENCIA", "ORGANIZACION"}:
            raise ValueError("tipo de verificación inválido")
        return value


class AppointmentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: UUID = Field(alias="requestId")
    starts_at: datetime = Field(alias="startsAt")
    ends_at: datetime = Field(alias="endsAt")
    cost_mxn: float = Field(alias="costMxn", ge=0)
    confirmed_by_provider: bool = Field(alias="confirmedByProvider")
    is_visit: bool | None = Field(default=None, alias="isVisit")


class AppointmentPatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    starts_at: datetime | None = Field(default=None, alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    confirmed_by_client: bool | None = Field(default=None, alias="confirmedByClient")
    confirmed_by_provider: bool | None = Field(default=None, alias="confirmedByProvider")
    reason: str | None = None


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1)


class Material(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str
    quantity: float = Field(gt=0)
    unit: str
    unit_price_mxn: float = Field(alias="unitPriceMxn", ge=0)
    subtotal_mxn: float = Field(alias="subtotalMxn", ge=0)
    brand_or_quality: str | None = Field(default=None, alias="brandOrQuality")


class ProposalCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: UUID = Field(alias="requestId")
    work_description: str = Field(alias="workDescription", min_length=1)
    dates: list[date] = Field(default_factory=list)
    labor_subtotal_mxn: float = Field(alias="laborSubtotalMxn", ge=0)
    materials: list[Material] = Field(default_factory=list)
    additional_costs_mxn: float = Field(alias="additionalCostsMxn", ge=0)
    total_mxn: float = Field(alias="totalMxn", ge=0)

    @model_validator(mode="after")
    def validate_total(self):
        materials_total = sum(item.subtotal_mxn for item in self.materials)
        expected = round(self.labor_subtotal_mxn + materials_total + self.additional_costs_mxn, 2)
        if round(self.total_mxn, 2) != expected:
            raise ValueError("la suma de materiales, mano de obra y extras no coincide")
        for item in self.materials:
            if round(item.quantity * item.unit_price_mxn, 2) != round(item.subtotal_mxn, 2):
                raise ValueError("el subtotal de un material no coincide")
        return self


class ProposalDecision(BaseModel):
    decision: str
    comment: str | None = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in {"ACEPTAR", "PEDIR_CAMBIOS", "RECHAZAR"}:
            raise ValueError("decisión inválida")
        return value


class ChangeCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: UUID = Field(alias="requestId")
    type: str
    reason: str = Field(min_length=1)
    amount_delta_mxn: float = Field(alias="amountDeltaMxn")
    updated_total_mxn: float = Field(alias="updatedTotalMxn", ge=0)
    affected_items: list[str] = Field(alias="affectedItems", min_length=1)
    proposed_date: date = Field(alias="proposedDate")
    initiated_by: str | None = Field(default=None, alias="initiatedBy")

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"COSTO", "MATERIAL", "ALCANCE", "FECHA"}:
            raise ValueError("tipo de cambio inválido")
        return value


class ChangeDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    decision: str
    updated_terms: ChangeCreate | None = Field(default=None, alias="updatedTerms")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in {"ACEPTAR", "RECHAZAR", "CONTRAPROPONER"}:
            raise ValueError("decisión inválida")
        return value


class EvaluationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject_type: str = Field(alias="subjectType")
    punctuality: int | None = Field(default=None, ge=1, le=5)
    quality: int | None = Field(default=None, ge=1, le=5)
    cleanliness: int | None = Field(default=None, ge=1, le=5)
    budget_adherence: int | None = Field(default=None, ge=1, le=5)
    score: int = Field(ge=1, le=5)
    comment: str | None = None

    @field_validator("subject_type")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        if value not in {"PROVEEDOR", "CLIENTE"}:
            raise ValueError("sujeto de evaluación inválido")
        return value


class PrivacyRequestCreate(BaseModel):
    type: PrivacyType
    correctedValues: dict[str, str] | None = None


class PrivacyFulfillment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    action: str
    corrected_values: dict[str, str] | None = Field(default=None, alias="correctedValues")
    response_note: str | None = Field(default=None, alias="responseNote")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if value not in {"EXPORT_JSON_PDF", "RECTIFICAR", "ANONIMIZAR", "RESPONDER"}:
            raise ValueError("acción ARCO inválida")
        return value


class StatusPatch(BaseModel):
    status: ProjectStatus
    reason: str | None = None


class ContactRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    expected_outcome: str = Field(alias="expectedOutcome", min_length=1)
    approximate_zone: str = Field(alias="approximateZone", min_length=1)
    trade: str | None = None
    desired_date: date | None = Field(default=None, alias="desiredDate")
    description: str | None = None

    @field_validator("desired_date")
    @classmethod
    def validate_desired_date(cls, value: date | None) -> date | None:
        return _reject_past_desired_date(value)


class OAuthExchange(BaseModel):
    code: str = Field(min_length=8, max_length=128)


class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100, alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)


def page_info(page: int, page_size: int, total_items: int) -> dict[str, Any]:
    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return {
        "page": page,
        "pageSize": page_size,
        "totalItems": total_items,
        "totalPages": total_pages,
    }
