"""Carga datos de demostración en la base configurada por DATABASE_URL.

Uso local:
    python -m app.seed

Uso con Docker:
    docker compose run --rm api python -m app.seed
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
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
from .obra import obra_svg
from .security import hash_password
from .storage import put_object


def seed() -> None:
    if get_settings().app_env not in {"development", "test"}:
        raise SystemExit("Los datos demo solo se cargan en development o test.")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(
            select(User).where(User.email == "demo.cliente@example.com")
        )
        if existing is None:
            _seed_core(db)
        _seed_gallery(db)
        db.commit()
        print("Datos de demostración listos para el índice público.")
        print(
            "Usuarios demo: demo.cliente@example.com, "
            "demo.proveedor@example.com, demo.admin@example.com"
        )
        print("Contraseña demo: DemoPass123!")
    finally:
        db.close()


def _seed_core(db: Session) -> None:
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
                AvailabilitySlot(weekday=1, starts_at="08:00", ends_at="18:00"),
                AvailabilitySlot(weekday=6, starts_at="09:00", ends_at="14:00"),
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
    db.flush()


GALLERY = (
    {
        "email": "demo.albanil@example.com",
        "name": "Doña Lucha Albañilería",
        "modality": ProviderModality.TRABAJADOR,
        "trades": ["albanileria", "impermeabilizacion"],
        "zone": "Coyoacán",
        "years": 14,
        "price": 1800,
        "works": [
            ("Resanar humedad del cuarto de atrás", "muro-resanado.svg"),
            ("Levantar pretil de azotea", "pretil-azotea.svg"),
        ],
        "score": 5,
    },
    {
        "email": "demo.plomero@example.com",
        "name": "Taller de Llaves Narvarte",
        "modality": ProviderModality.ORGANIZACION,
        "trades": ["plomeria"],
        "zone": "Benito Juárez",
        "years": 9,
        "price": 950,
        "works": [
            ("Cambiar el tinaco y dejar de fugar", "tinaco-nuevo.svg"),
            ("Dejar de gotear el lavabo del baño", "lavabo-sello.svg"),
        ],
        "score": 4,
    },
    {
        "email": "demo.electrico@example.com",
        "name": "Circuitos del Sur",
        "modality": ProviderModality.TRABAJADOR,
        "years": 11,
        "price": 1100,
        "zone": "Xochimilco",
        "trades": ["electricidad"],
        "works": [
            ("Cambiar tablero y dejar contactos seguros", "tablero-obra.svg"),
        ],
        "score": 5,
    },
    {
        "email": "demo.herrero@example.com",
        "name": "Herrería La Palma",
        "modality": ProviderModality.ORGANIZACION,
        "years": 16,
        "price": 2200,
        "zone": "Iztapalapa",
        "trades": ["herreria"],
        "works": [
            ("Reja de patio que sí cierra", "reja-patio.svg"),
            ("Barandal de escalera", "barandal.svg"),
        ],
        "score": 5,
    },
)


def _add_work_photo(
    db: Session,
    *,
    owner: User,
    provider: Provider,
    trade: str,
    zone: str,
    title: str,
    filename: str,
    variant: int,
    now: datetime,
) -> None:
    key = f"demo/obra/{provider.id}/{filename}"
    put_object(key, obra_svg(title, trade, zone, variant=variant))
    work = ServiceRequest(
        owner_id=owner.id,
        selected_provider_id=provider.id,
        status=ProjectStatus.CONCLUIDO,
        expected_outcome=title,
        trade=trade,
        approximate_zone=zone,
        description="Proyecto de muestra para el índice. Sin domicilio exacto.",
        concluded_at=now,
        confirmed_at=now - timedelta(days=20),
    )
    db.add(work)
    db.flush()
    db.add(
        StoredFile(
            request_id=work.id,
            provider_id=provider.id,
            owner_id=owner.id,
            file_type=FileType.IMAGE,
            file_name=filename,
            object_key=key,
            mime_type="image/svg+xml",
            size_bytes=len(obra_svg(title, trade, zone, variant=variant)),
        )
    )


def _seed_gallery(db: Session) -> None:
    now = datetime.utcnow()
    client = db.scalar(select(User).where(User.email == "demo.cliente@example.com"))
    if client is None:
        return
    demo_provider = db.scalar(
        select(Provider).where(Provider.name == "Construcciones Demo MX")
    )
    if demo_provider is not None and not demo_provider.portfolio_files:
        title = "Pintar la sala después de la humedad"
        _add_work_photo(
            db,
            owner=client,
            provider=demo_provider,
            trade="albanileria",
            zone="Coyoacán",
            title=title,
            filename="sala-pintada.svg",
            variant=0,
            now=now,
        )
        cover_key = f"demo/portfolio/{demo_provider.id}/portada.svg"
        put_object(cover_key, obra_svg("Portafolio", "pintura", "Coyoacán", variant=2))
        db.add(
            StoredFile(
                provider_id=demo_provider.id,
                owner_id=demo_provider.account_id,
                file_type=FileType.IMAGE,
                file_name="portafolio.svg",
                object_key=cover_key,
                mime_type="image/svg+xml",
                size_bytes=1200,
            )
        )
    for index, item in enumerate(GALLERY):
        if db.scalar(select(User).where(User.email == item["email"])) is not None:
            continue
        account = User(
            email=item["email"],
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.PROVEEDOR,
            name=item["name"],
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        db.add(account)
        db.flush()
        provider = Provider(
            account_id=account.id,
            name=item["name"],
            modality=item["modality"],
            experience_years=item["years"],
            general_availability="Lunes a sábado, 08:00-18:00",
            reference_price_mxn=item["price"],
            guarantee_months=6,
            trades=[ProviderTrade(trade=trade) for trade in item["trades"]],
            coverage=[ProviderCoverage(zone=item["zone"])],
            verifications=[
                Verification(
                    verification_type="IDENTIDAD",
                    status=VerificationStatus.VERIFICADA,
                    reviewed_at=now,
                )
            ],
        )
        db.add(provider)
        db.flush()
        cover_key = f"demo/portfolio/{provider.id}/portada.svg"
        put_object(
            cover_key,
            obra_svg(item["name"], item["trades"][0], item["zone"], variant=index),
        )
        db.add(
            StoredFile(
                provider_id=provider.id,
                owner_id=account.id,
                file_type=FileType.IMAGE,
                file_name="portada.svg",
                object_key=cover_key,
                mime_type="image/svg+xml",
                size_bytes=1400,
            )
        )
        for variant, (title, filename) in enumerate(item["works"]):
            _add_work_photo(
                db,
                owner=client,
                provider=provider,
                trade=item["trades"][0],
                zone=item["zone"],
                title=title,
                filename=filename,
                variant=variant + index,
                now=now - timedelta(days=10 + variant),
            )
        first_work = db.scalars(
            select(ServiceRequest).where(
                ServiceRequest.selected_provider_id == provider.id
            )
        ).first()
        if first_work is not None:
            db.add(
                Evaluation(
                    request_id=first_work.id,
                    author_id=client.id,
                    provider_id=provider.id,
                    score=item["score"],
                    punctuality=item["score"],
                    quality=item["score"],
                    cleanliness=max(item["score"] - 1, 3),
                    budget_adherence=item["score"],
                    comment="Trabajo de muestra para el índice público.",
                    status=EvaluationStatus.PUBLICADA,
                )
            )


if __name__ == "__main__":
    seed()
