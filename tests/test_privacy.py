from app.main import app
from tests.helpers import admin_token, auth_header, token_for


def test_privacy_request_and_admin_report():
    with app.test_client() as client:
        token = token_for(client, "cli@example.com")
        created = client.post(
            "/api/v1/privacy/requests",
            headers=auth_header(token),
            json={"type": "ACCESO"},
        )
        folio = created.get_json()["folio"]
        fulfilled = client.post(
            f"/api/v1/privacy/requests/{folio}/fulfillment",
            headers=auth_header(admin_token()),
            json={"action": "RESPONDER", "responseNote": "Exportación lista"},
        )
        report = client.get(
            "/api/v1/admin/availability-reports?month=2026-10",
            headers=auth_header(admin_token()),
        )
        forbidden = client.get(
            "/api/v1/admin/availability-reports?month=2026-10",
            headers=auth_header(token),
        )

    assert created.status_code == 201
    assert fulfilled.status_code == 200
    assert fulfilled.get_json()["status"] == "RESPONDIDA"
    assert report.status_code == 200
    assert report.get_json()["availabilityPercent"] == 100
    assert forbidden.status_code == 403
