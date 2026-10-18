from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_returns_ok():
    responde = client.get("/health")

    assert responde.status_code == 200
    assert responde.json() == {"status": "ok"}