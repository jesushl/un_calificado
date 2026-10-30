"""Carga datos de demostración en la base configurada por DATABASE_URL.

Uso local:
    python -m app.seed

Uso con Docker:
    docker compose run --rm api python -m app.seed
"""

from datetime import datetime, timedelta

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import (
    Appointment,
    AppointmentStatus,
    AuditEvent,
    Availability,
    AvailabilitySlot,
    BudgetVersion,
    Consent,
    Evaluation,
    EvaluationStatus,
    FileType,
    Message,
    ProjectStatus,
    Proposal,
    ProposalStatus,
    Provider,
    ProviderCoverage,
    ProviderModality,
    ProviderTrade,
    ServiceRequest,
    StoredFile,
    User,
    UserRole,
    Verification,
    VerificationStatus,
)
from .security import hash_password


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(User).where(User.email == "demo.cliente@example.com")
        )
        if existing is not None:
            print("Los datos de demostración ya existen.")
            return

        now = datetime.utcnow()
        client = User(
            email="demo.cliente@example.com",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.CLIENTE,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        provider_user = User(
            email="demo.proveedor@example.com",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.PROVEEDOR,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        admin = User(
            email="demo.admin@example.com",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.ADMINISTRADOR,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        db.add_all([client, provider_user, admin])
        db.flush()

        provider = Provider(
            account_id=provider_user.id,
            name="Construcciones Demo MX",
            modality=ProviderModality.ORGANIZACION,
            experience_years=8,
            general_availability="Lunes a sábado, 08:00-18:00",
            trades=[
                ProviderTrade(trade="albanileria"),
                ProviderTrade(trade="plomeria"),
            ],
            coverage=[
                ProviderCoverage(zone="Coyoacán"),
                ProviderCoverage(zone="Benito Juárez"),
            ],
            availability=Availability(
                general_status="DECLARADA",
                slots=[
                    AvailabilitySlot(
                        weekday=1, starts_at="08:00", ends_at="18:00"
                    ),
                    AvailabilitySlot(
                        weekday=6, starts_at="09:00", ends_at="14:00"
                    ),
                ],
            ),
            verifications=[
                Verification(
                    verification_type="ORGANIZACION",
                    status=VerificationStatus.VERIFICADA,
                    reviewed_at=now,
                )
            ],
        )
        db.add(provider)
        db.flush()

        request = ServiceRequest(
            owner_id=client.id,
            selected_provider_id=provider.id,
            status=ProjectStatus.CONFIRMADA,
            expected_outcome="Reparar humedad y pintar la sala",
            trade="albanileria",
            approximate_zone="Coyoacán",
            description="Humedad en muro norte y pintura deteriorada.",
            desired_date=(now + timedelta(days=14)).date(),
            confirmed_at=now,
        )
        db.add(request)
        db.flush()

        db.add_all(
            [
                Consent(
                    user_id=client.id,
                    privacy_version="2026-01",
                    adult_declaration=True,
                ),
                StoredFile(
                    request_id=request.id,
                    owner_id=client.id,
                    file_type=FileType.IMAGE,
                    file_name="muro-sala.jpg",
                    object_key="demo/requests/muro-sala-example.jpg",
                    mime_type="image/jpeg",
                    size_bytes=245_760,
                ),
                Appointment(
                    request_id=request.id,
                    provider_id=provider.id,
                    status=AppointmentStatus.CONFIRMADA,
                    starts_at=now + timedelta(days=7),
                    ends_at=now + timedelta(days=7, hours=2),
                    cost_mxn=350.00,
                    is_visit=True,
                ),
                Message(
                    request_id=request.id,
                    sender_id=client.id,
                    content="¿Podemos revisar también la moldura de la ventana?",
                ),
                Evaluation(
                    request_id=request.id,
                    author_id=client.id,
                    provider_id=provider.id,
                    score=5,
                    punctuality=5,
                    quality=5,
                    cleanliness=4,
                    budget_adherence=5,
                    comment="Perfil de demostración; evaluación de ejemplo.",
                    status=EvaluationStatus.PUBLICADA,
                ),
                AuditEvent(
                    request_id=request.id,
                    actor_id=client.id,
                    action="SOLICITUD_CONFIRMADA",
                ),
            ]
        )

        proposal = Proposal(
            request_id=request.id,
            provider_id=provider.id,
            version=1,
            status=ProposalStatus.ENVIADA,
            work_description="Resanar, sellar humedad y aplicar dos manos de pintura.",
            total_mxn=4850.00,
            issued_at=now,
            expires_at=now + timedelta(days=5),
            budget_versions=[
                BudgetVersion(
                    number=1,
                    total_mxn=4850.00,
                    difference_from_initial_mxn=0,
                )
            ],
        )
        db.add(proposal)
        db.commit()
        print("Datos de demostración creados.")
        print("Usuarios demo: demo.cliente@example.com, "
              "demo.proveedor@example.com, demo.admin@example.com")
        print("Contraseña demo: DemoPass123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
