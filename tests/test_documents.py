from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from app.main import app, create_app

client = TestClient(app)


def headers(user):
    return {"Authorization": f"Bearer {user}-token"}


@pytest.mark.parametrize(
    "user,document_id,status",
    [
        ("alice", 1, 200),
        ("alice", 2, 404),
        ("bob", 2, 200),
        ("bob", 1, 404),
        ("admin", 1, 200),
        ("admin", 2, 200),
        ("alice", 999, 404),
        ("admin", 999, 404),
    ],
)
def test_document_read_permissions(user, document_id, status):
    response = client.get(f"/documents/{document_id}", headers=headers(user))
    assert response.status_code == status
    if status == 200:
        assert response.json()["id"] == document_id


@pytest.mark.parametrize(
    "user,document_id",
    [
        ("alice", 1),
        ("alice", 2),
        ("bob", 1),
        ("bob", 2),
    ],
)
def test_regular_users_cannot_delete(user, document_id):
    response = client.delete(f"/documents/{document_id}", headers=headers(user))
    assert response.status_code == 403
    assert (
        client.get(f"/documents/{document_id}", headers=headers("admin")).status_code
        == 200
    )


@pytest.mark.parametrize("document_id", [1, 2])
def test_admin_deletes_document(document_id):
    response = client.delete(f"/documents/{document_id}", headers=headers("admin"))
    assert response.status_code == 204
    assert response.content == b""
    assert (
        client.get(f"/documents/{document_id}", headers=headers("admin")).status_code
        == 404
    )
    assert (
        client.delete(f"/documents/{document_id}", headers=headers("admin")).status_code
        == 404
    )


def test_admin_delete_missing_document():
    assert client.delete("/documents/999", headers=headers("admin")).status_code == 404


def test_concurrent_admin_deletion_returns_safe_statuses():
    barrier = Barrier(2)

    class ConcurrentDocuments(dict):
        def get(self, key, default=None):
            document = super().get(key, default)
            barrier.wait(timeout=5)
            return document

    application = create_app(include_ui=False)
    application.state.documents = ConcurrentDocuments(application.state.documents)
    with TestClient(application, raise_server_exceptions=False) as test_client:

        def delete():
            return test_client.delete(
                "/documents/1", headers=headers("admin")
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: delete(), range(2)))
    assert sorted(statuses) == [204, 404]


@pytest.mark.parametrize("method", ["get", "delete"])
@pytest.mark.parametrize(
    "authorization",
    [None, "Bearer unknown-token", "Basic alice-token", "Bearer"],
    ids=["missing", "unknown", "wrong-scheme", "empty-bearer"],
)
def test_authentication_applies_to_both_routes(method, authorization):
    response = getattr(client, method)(
        "/documents/1",
        headers={} if authorization is None else {"Authorization": authorization},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
