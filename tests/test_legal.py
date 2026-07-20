from fastapi.testclient import TestClient

from app.main import app


def test_privacy_policy_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/privacy")

    assert response.status_code == 200
    assert "AI Sales Agent Privacy Policy" in response.text
    assert "/data-deletion" in response.text


def test_data_deletion_instructions_are_available() -> None:
    with TestClient(app) as client:
        response = client.get("/data-deletion")

    assert response.status_code == 200
    assert "Delete my data" in response.text
