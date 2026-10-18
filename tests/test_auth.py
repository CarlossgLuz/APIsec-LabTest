from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_documents_requires_authentication():
    response = client.get("/documents/1")

    assert response.status_code == 401
