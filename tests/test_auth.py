from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_documents_requires_authentication():
    response = client.get(
        "/documents/1",
        )

    assert response.status_code == 401

def test_documents_rejects_invalid_token():
    response = client.get(
        "/documents/1",
        headers={"Authorization": "Bearer token-invalido"}
        )

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"
    assert response.json()["detail"] == "Invalid token"
