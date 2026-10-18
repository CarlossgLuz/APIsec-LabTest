import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from lab.vulnerable_app import create_vulnerable_app


@pytest.mark.parametrize(
    "user,document_id",
    [("alice", 1), ("bob", 2), ("admin", 1), ("admin", 2)],
)
def test_bopla_internal_property_is_filtered_for_every_identity(user, document_id):
    headers = {"Authorization": f"Bearer {user}-token"}
    with (
        TestClient(create_vulnerable_app()) as vulnerable,
        TestClient(create_app()) as secure,
    ):
        exposed = vulnerable.get(f"/documents/{document_id}", headers=headers)
        protected = secure.get(f"/documents/{document_id}", headers=headers)

        assert exposed.status_code == protected.status_code == 200
        assert exposed.json()["internal_notes"].startswith("Synthetic internal review:")
        assert "internal_notes" not in protected.json()
        assert protected.json() == {
            key: value
            for key, value in exposed.json().items()
            if key != "internal_notes"
        }
        assert "internal_notes" in secure.app.state.documents[document_id]


@pytest.mark.parametrize(
    "headers,status",
    [
        ({}, 401),
        ({"Authorization": "Bearer unknown-token"}, 401),
        ({"Authorization": "Bearer bob-token"}, 404),
    ],
)
def test_bopla_does_not_bypass_authentication_or_ownership(headers, status):
    with TestClient(create_app()) as client:
        response = client.get("/documents/1", headers=headers)
    assert response.status_code == status
    assert "internal_notes" not in response.text


def test_document_schema_excludes_internal_property():
    schema = create_app().openapi()["components"]["schemas"]["PublicDocument"]
    assert set(schema["properties"]) == {"id", "owner_id", "title", "content"}


def test_secure_application_instances_have_independent_state():
    headers = {"Authorization": "Bearer admin-token"}
    with TestClient(create_app()) as first, TestClient(create_app()) as second:
        assert first.delete("/documents/2", headers=headers).status_code == 204
        assert first.get("/documents/2", headers=headers).status_code == 404
        assert second.get("/documents/2", headers=headers).status_code == 200
        first.app.state.documents[1]["internal_notes"] = "changed"
        assert second.app.state.documents[1]["internal_notes"] != "changed"
