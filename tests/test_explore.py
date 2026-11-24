from app.database import SessionLocal
from app.main import app
from app.models import (
    Evaluation,
    EvaluationStatus,
    FileType,
    ProjectStatus,
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
from app.obra import obra_svg
from app.security import hash_password
from app.storage import put_object
from tests.helpers import auth_header, token_for


def _gallery_provider():
    db = SessionLocal()
    try:
        owner = User(
            email="obra.cliente@example.com",
            password_hash=hash_password("correct-password"),
            role=UserRole.CLIENTE,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        account = User(
            email="obra.prov@example.com",
            password_hash=hash_password("correct-password"),
            role=UserRole.PROVEEDOR,
            privacy_consent_version="2026-01",
            adult_declaration=True,
        )
        db.add_all([owner, account])
        db.flush()
        provider = Provider(
            account_id=account.id,
            name="Herrería La Palma",
            modality=ProviderModality.ORGANIZACION,
            experience_years=12,
            trades=[ProviderTrade(trade="herreria")],
            coverage=[ProviderCoverage(zone="Iztapalapa")],
            verifications=[
                Verification(
                    verification_type="IDENTIDAD",
                    status=VerificationStatus.VERIFICADA,
                )
            ],
        )
        db.add(provider)
        db.flush()
        work = ServiceRequest(
            owner_id=owner.id,
            selected_provider_id=provider.id,
            status=ProjectStatus.CONCLUIDO,
            expected_outcome="Reja de patio que sí cierra",
            trade="herreria",
            approximate_zone="Iztapalapa",
        )
        db.add(work)
        db.flush()
        key = f"test/obra/{provider.id}/reja.svg"
        put_object(key, obra_svg("Reja de patio que sí cierra", "herreria", "Iztapalapa"))
        db.add(
            StoredFile(
                request_id=work.id,
                provider_id=provider.id,
                owner_id=account.id,
                file_type=FileType.IMAGE,
                file_name="reja.svg",
                object_key=key,
                mime_type="image/svg+xml",
                size_bytes=800,
            )
        )
        db.add(
            Evaluation(
                request_id=work.id,
                author_id=owner.id,
                provider_id=provider.id,
                score=5,
                status=EvaluationStatus.PUBLICADA,
            )
        )
        db.commit()
        return str(provider.id)
    finally:
        db.close()


def test_explore_is_public_and_hides_exact_address():
    provider_id = _gallery_provider()
    with app.test_client() as client:
        popular = client.get("/api/v1/explore/providers")
        works = client.get("/api/v1/explore/works")
        detail = client.get(f"/api/v1/explore/providers/{provider_id}")
        contact = client.post(
            f"/api/v1/explore/providers/{provider_id}",
            json={
                "expectedOutcome": "Quiero una reja",
                "approximateZone": "Coyoacán",
            },
        )

    assert popular.status_code == 200
    assert popular.get_json()["items"][0]["name"] == "Herrería La Palma"
    assert "address" not in popular.get_json()["items"][0]
    assert popular.get_json()["items"][0]["verified"] is True
    assert works.status_code == 200
    assert works.get_json()["items"][0]["expectedOutcome"] == "Reja de patio que sí cierra"
    assert works.get_json()["items"][0]["approximateZone"] == "Iztapalapa"
    assert detail.status_code == 200
    assert contact.status_code == 401


def test_client_can_contact_and_provider_cannot():
    provider_id = _gallery_provider()
    with app.test_client() as client:
        client_token = token_for(client, "cliente.contacto@example.com")
        provider_token = token_for(client, "otro.prov@example.com", "PROVEEDOR")
        forbidden = client.post(
            f"/api/v1/explore/providers/{provider_id}",
            headers=auth_header(provider_token),
            json={
                "expectedOutcome": "Quiero una reja",
                "approximateZone": "Coyoacán",
            },
        )
        created = client.post(
            f"/api/v1/explore/providers/{provider_id}",
            headers=auth_header(client_token),
            json={
                "expectedOutcome": "Quiero una reja para el patio",
                "approximateZone": "Coyoacán",
                "trade": "herreria",
            },
        )

    assert forbidden.status_code == 403
    assert created.status_code == 201
    assert created.get_json()["selectedProviderId"] == provider_id
    assert created.get_json()["approximateZone"] == "Coyoacán"


def test_discovery_radius_hides_providers_outside_the_alcaldia():
    _gallery_provider()
    with app.test_client() as client:
        nearby = client.get("/api/v1/explore/providers?zona=Coyoacán&radioKm=5")
        farther = client.get("/api/v1/explore/providers?zona=Coyoacán&radioKm=20")
        zones = client.get("/api/v1/explore/zones")

    names_near = [item["name"] for item in nearby.get_json()["items"]]
    names_far = [item["name"] for item in farther.get_json()["items"]]
    assert nearby.status_code == 200
    assert "Herrería La Palma" not in names_near
    assert nearby.get_json()["discovery"]["applied"] is True
    assert farther.status_code == 200
    assert "Herrería La Palma" in names_far
    assert any(item["id"] == "Coyoacán" for item in zones.get_json()["items"])


def test_account_discovery_settings_filter_explore():
    provider_id = _gallery_provider()
    with app.test_client() as client:
        token = token_for(client, "ana.zona@example.com")
        saved = client.patch(
            "/api/v1/users/me",
            headers=auth_header(token),
            json={"searchZone": "Coyoacán", "maxDistanceKm": 5},
        )
        filtered = client.get(
            "/api/v1/explore/providers",
            headers=auth_header(token),
        )
        wide = client.patch(
            "/api/v1/users/me",
            headers=auth_header(token),
            json={"maxDistanceKm": 20},
        )
        listed = client.get(
            "/api/v1/explore/providers",
            headers=auth_header(token),
        )

    assert saved.status_code == 200
    assert saved.get_json()["searchZone"] == "Coyoacán"
    assert saved.get_json()["maxDistanceKm"] == 5
    assert provider_id not in [item["id"] for item in filtered.get_json()["items"]]
    assert wide.status_code == 200
    assert any(item["id"] == provider_id for item in listed.get_json()["items"])


def test_signed_work_photo_is_public():
    _gallery_provider()
    with app.test_client() as client:
        works = client.get("/api/v1/explore/works").get_json()["items"]
        photo = client.get(works[0]["downloadUrl"])

    assert photo.status_code == 200
    assert photo.mimetype == "image/svg+xml"
    assert b"<svg" in photo.data


def test_local_search_filters_providers_and_works_by_text():
    _gallery_provider()
    with app.test_client() as client:
        by_name = client.get("/api/v1/explore/providers?q=Palma")
        by_trade = client.get("/api/v1/explore/providers?q=herrero")
        by_work = client.get("/api/v1/explore/works?q=reja")
        miss = client.get("/api/v1/explore/providers?q=plomeria+azotea")

    assert by_name.status_code == 200
    assert any(item["name"] == "Herrería La Palma" for item in by_name.get_json()["items"])
    assert by_name.get_json()["query"] == "Palma"
    assert by_trade.status_code == 200
    assert any(item["name"] == "Herrería La Palma" for item in by_trade.get_json()["items"])
    assert by_work.status_code == 200
    assert any("reja" in item["expectedOutcome"].lower() for item in by_work.get_json()["items"])
    assert miss.status_code == 200
    assert miss.get_json()["items"] == []
    assert "Nada coincide" in (miss.get_json()["noResultsMessage"] or "")
