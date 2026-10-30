from datetime import date

from app.main import app
from tests.helpers import auth_header, token_for
from tests.test_providers import PROFILE


def _create_provider(client):
    token = token_for(client, "prov@example.com", "PROVEEDOR")
    created = client.post("/api/v1/providers", headers=auth_header(token), json=PROFILE)
    return token, created.get_json()["id"]


def test_request_search_selection_and_privacy_zone():
    with app.test_client() as client:
        client_token = token_for(client, "cli@example.com")
        provider_token, provider_id = _create_provider(client)
        created = client.post(
            "/api/v1/requests",
            headers=auth_header(client_token),
            json={
                "expectedOutcome": "Reparar reja",
                "trade": "herreria",
                "approximateZone": "Coyoacán",
                "desiredDate": date.today().isoformat(),
                "description": "Reja del patio",
                "manualCapture": True,
            },
        )
        request_id = created.get_json()["id"]
        confirmed = client.patch(
            f"/api/v1/requests/{request_id}",
            headers=auth_header(client_token),
            json={"summaryConfirmed": True},
        )
        search = client.post(
            f"/api/v1/requests/{request_id}/search",
            headers=auth_header(client_token),
            json={"sort": "rating"},
        )
        selected = client.put(
            f"/api/v1/requests/{request_id}/selection",
            headers=auth_header(client_token),
            json={"providerId": provider_id},
        )
        privacy = client.get(
            f"/api/v1/requests/{request_id}/privacy",
            headers=auth_header(provider_token),
        )
        foreign = token_for(client, "otro@example.com", "PROVEEDOR")
        denied = client.get(
            f"/api/v1/requests/{request_id}/privacy",
            headers=auth_header(foreign),
        )

    assert created.status_code == 201
    assert confirmed.get_json()["status"] == "CONFIRMADA"
    assert search.status_code == 200
    assert search.get_json()["items"]
    assert selected.get_json()["selectedProviderId"] == provider_id
    assert privacy.get_json()["visibility"] == "ZONA_APROXIMADA"
    assert privacy.get_json()["exactAddress"] is None
    assert denied.status_code == 403


def test_messages_reject_phones_until_appointment_exists():
    with app.test_client() as client:
        client_token = token_for(client, "cli2@example.com")
        created = client.post(
            "/api/v1/requests",
            headers=auth_header(client_token),
            json={
                "expectedOutcome": "Pintar sala",
                "trade": "pintura",
                "approximateZone": "Coyoacán",
            },
        )
        request_id = created.get_json()["id"]
        blocked = client.post(
            f"/api/v1/requests/{request_id}/messages",
            headers=auth_header(client_token),
            json={"content": "Hola, mi teléfono es 5512345678"},
        )

    assert blocked.status_code in {403, 422}
