from app.main import app
from tests.helpers import admin_token, auth_header, token_for


PROFILE = {
    "name": "Herrería Norte",
    "modality": "TRABAJADOR",
    "trades": ["herreria"],
    "experienceYears": 6,
    "coverage": ["Coyoacán"],
    "generalAvailability": "Lunes a viernes",
    "referencePriceMxn": 1200,
    "guaranteeMonths": 12,
}


def test_provider_profile_portfolio_and_verification_review():
    with app.test_client() as client:
        provider_token = token_for(client, "prov@example.com", "PROVEEDOR")
        client_token = token_for(client, "cli@example.com")
        created = client.post(
            "/api/v1/providers",
            headers=auth_header(provider_token),
            json=PROFILE,
        )
        provider_id = created.get_json()["id"]
        listed = client.get(
            "/api/v1/providers?oficio=herreria&zona=Coyoacán",
            headers=auth_header(client_token),
        )
        portfolio = client.post(
            f"/api/v1/providers/{provider_id}/portfolio",
            headers=auth_header(provider_token),
            json={
                "fileName": "reja.png",
                "contentType": "image/png",
                "sizeBytes": 2048,
                "objectKey": "demo/portfolio/reja.png",
            },
        )
        file_id = portfolio.get_json()["id"]
        verification = client.post(
            f"/api/v1/providers/{provider_id}/verifications",
            headers=auth_header(provider_token),
            json={"type": "IDENTIDAD", "fileId": file_id},
        )
        review = client.patch(
            f"/api/v1/providers/{provider_id}/verifications/{verification.get_json()['id']}",
            headers=auth_header(admin_token()),
            json={"status": "VERIFICADA"},
        )

    assert created.status_code == 201
    assert listed.status_code == 200
    assert listed.get_json()["items"][0]["name"] == "Herrería Norte"
    assert "address" not in listed.get_json()["items"][0]
    assert portfolio.status_code == 201
    assert verification.status_code == 201
    assert review.status_code == 200
    assert review.get_json()["status"] == "VERIFICADA"
