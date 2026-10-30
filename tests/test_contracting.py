from datetime import date, datetime, timedelta, timezone

from app.main import app
from tests.helpers import auth_header, token_for
from tests.test_providers import PROFILE


def test_appointment_proposal_change_and_evaluation_flow():
    with app.test_client() as client:
        client_token = token_for(client, "cli@example.com")
        provider_token = token_for(client, "prov@example.com", "PROVEEDOR")
        provider_id = client.post(
            "/api/v1/providers",
            headers=auth_header(provider_token),
            json=PROFILE,
        ).get_json()["id"]
        request_id = client.post(
            "/api/v1/requests",
            headers=auth_header(client_token),
            json={
                "expectedOutcome": "Reparar reja",
                "trade": "herreria",
                "approximateZone": "Coyoacán",
                "desiredDate": date.today().isoformat(),
                "description": "Reja del patio",
            },
        ).get_json()["id"]
        client.patch(
            f"/api/v1/requests/{request_id}",
            headers=auth_header(client_token),
            json={"summaryConfirmed": True},
        )
        client.put(
            f"/api/v1/requests/{request_id}/selection",
            headers=auth_header(client_token),
            json={"providerId": provider_id},
        )
        client.post(
            f"/api/v1/requests/{request_id}/provider-decision",
            headers=auth_header(provider_token),
            json={"decision": "ACEPTAR"},
        )
        starts = datetime.now(timezone.utc) + timedelta(days=2)
        appointment = client.post(
            "/api/v1/appointments",
            headers=auth_header(provider_token),
            json={
                "requestId": request_id,
                "startsAt": starts.isoformat(),
                "endsAt": (starts + timedelta(hours=2)).isoformat(),
                "costMxn": 350,
                "confirmedByProvider": True,
                "isVisit": True,
            },
        )
        confirmed = client.patch(
            f"/api/v1/appointments/{appointment.get_json()['id']}",
            headers=auth_header(client_token),
            json={"confirmedByClient": True},
        )
        proposal = client.post(
            "/api/v1/proposals",
            headers=auth_header(provider_token),
            json={
                "requestId": request_id,
                "workDescription": "Soldar y pintar",
                "laborSubtotalMxn": 1000,
                "materials": [
                    {
                        "description": "soldadura",
                        "quantity": 1,
                        "unit": "servicio",
                        "unitPriceMxn": 200,
                        "subtotalMxn": 200,
                    }
                ],
                "additionalCostsMxn": 50,
                "totalMxn": 1250,
            },
        )
        decided = client.post(
            f"/api/v1/proposals/{proposal.get_json()['id']}/decision",
            headers=auth_header(client_token),
            json={"decision": "ACEPTAR"},
        )
        started = client.patch(
            f"/api/v1/requests/{request_id}/status",
            headers=auth_header(provider_token),
            json={"status": "EN_PROCESO"},
        )
        finished = client.patch(
            f"/api/v1/requests/{request_id}/status",
            headers=auth_header(provider_token),
            json={"status": "TERMINADO"},
        )
        closed = client.patch(
            f"/api/v1/requests/{request_id}/status",
            headers=auth_header(client_token),
            json={"status": "CONCLUIDO"},
        )
        evaluation = client.post(
            f"/api/v1/requests/{request_id}/evaluations",
            headers=auth_header(client_token),
            json={"subjectType": "PROVEEDOR", "score": 5, "quality": 5},
        )
        analysis = client.post(
            f"/api/v1/changes",
            headers=auth_header(provider_token),
            json={
                "requestId": request_id,
                "type": "COSTO",
                "reason": "Material extra",
                "amountDeltaMxn": 100,
                "updatedTotalMxn": 1350,
                "affectedItems": ["soldadura"],
                "proposedDate": date.today().isoformat(),
            },
        )

    assert appointment.status_code == 201
    assert confirmed.get_json()["status"] == "CONFIRMADA"
    assert proposal.status_code == 201
    assert decided.get_json()["status"] == "ACEPTADA"
    assert started.get_json()["status"] == "EN_PROCESO"
    assert finished.get_json()["status"] == "TERMINADO"
    assert closed.get_json()["status"] == "CONCLUIDO"
    assert evaluation.status_code == 201
    assert analysis.status_code == 201
