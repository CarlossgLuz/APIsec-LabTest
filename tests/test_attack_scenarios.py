import pytest
from fastapi.testclient import TestClient

from app.main import app, documents
from lab.vulnerable_app import create_vulnerable_app

ALICE_HEADERS = {"Authorization": "Bearer alice-token"}
ADMIN_HEADERS = {"Authorization": "Bearer admin-token"}


@pytest.fixture
def vulnerable_client():
    with TestClient(create_vulnerable_app()) as client:
        yield client


def test_bola_reads_another_users_document(vulnerable_client):
    with TestClient(app) as secure_client:
        vulnerable_response = vulnerable_client.get("/documents/2", headers=ALICE_HEADERS)
        secure_response = secure_client.get("/documents/2", headers=ALICE_HEADERS)

    assert vulnerable_response.status_code == 200
    assert vulnerable_response.json()["owner_id"] == 2
    assert secure_response.status_code == 404
    assert secure_response.json() == {"detail": "Document not found"}


def test_bfla_deletes_another_users_document(vulnerable_client):
    vulnerable_response = vulnerable_client.delete("/documents/2", headers=ALICE_HEADERS)
    with TestClient(app) as secure_client:
        secure_response = secure_client.delete("/documents/2", headers=ALICE_HEADERS)
        assert secure_client.get("/documents/2", headers=ADMIN_HEADERS).status_code == 200

    assert vulnerable_response.status_code == 204
    assert vulnerable_response.content == b""
    assert vulnerable_client.get("/documents/2", headers=ADMIN_HEADERS).status_code == 404
    assert secure_response.status_code == 403


def test_lab_has_independent_document_copies(vulnerable_client):
    with TestClient(create_vulnerable_app()) as other_client:
        vulnerable_client.app.state.documents[2]["content"] = "changed"
        assert documents[2]["content"] != "changed"
        assert other_client.app.state.documents[2]["content"] != "changed"
        vulnerable_client.delete("/documents/2", headers=ALICE_HEADERS)
        assert other_client.get("/documents/2", headers=ALICE_HEADERS).status_code == 200
    assert 2 in documents


@pytest.mark.parametrize("method", ["get", "delete"])
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer unknown-token"}])
def test_vulnerable_app_still_requires_authentication(vulnerable_client, method, headers):
    response = getattr(vulnerable_client, method)("/documents/2", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert 2 in vulnerable_client.app.state.documents
