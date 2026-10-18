import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    with TestClient(create_app()) as test_client:
        yield test_client


def test_dashboard_and_local_assets(client):
    response = client.get("/")
    assert response.status_code == 200
    assert '<html lang="pt-BR">' in response.text
    assert 'id="run"' in response.text
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/lab.js").status_code == 200


def test_available_scenarios(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {"bola", "bfla", "bopla"}


@pytest.mark.parametrize("scenario", ["bola", "bfla", "bopla"])
def test_simulate_and_export_current_result(client, scenario, tmp_path):
    response = client.post(f"/api/simulations/{scenario}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["passed"] is True
    assert payload["result"]["simulation"] is True
    assert "Simulação controlada" in payload["markdown"]
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert len(list(tmp_path.glob("*.md"))) == 1
    assert "alice-token" not in response.text


def test_repeated_deletion_scenarios_are_independent(client):
    first = client.post("/api/simulations/bfla").json()["result"]
    second = client.post("/api/simulations/bfla").json()["result"]
    assert first["id"] != second["id"]
    assert first["vulnerable"]["status_code"] == 204
    assert second["vulnerable"]["status_code"] == 204


def test_unknown_scenario_does_not_write_reports(client, tmp_path):
    assert client.post("/api/simulations/unknown").status_code == 404
    assert list(tmp_path.iterdir()) == []


def test_missing_junit_does_not_claim_tests_passed(client):
    assert client.get("/api/test-status").json() == {"available": False}


def test_test_status_reads_junit(client, tmp_path):
    (tmp_path / "junit.xml").write_text(
        '<testsuites><testsuite tests="33" failures="1" errors="0" '
        'skipped="2"/></testsuites>',
        encoding="utf-8",
    )
    result = client.get("/api/test-status").json()
    assert result == {
        "available": True,
        "tests": 33,
        "failures": 1,
        "errors": 0,
        "skipped": 2,
        "source": "junit.xml",
    }


@pytest.mark.parametrize(
    "xml",
    [
        "not xml",
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><testsuite/>',
        '<testsuite tests="invalid"/>',
    ],
)
def test_invalid_junit_is_unavailable(client, tmp_path, xml):
    (tmp_path / "junit.xml").write_text(xml, encoding="utf-8")
    assert client.get("/api/test-status").json() == {"available": False}


def test_report_storage_failure_is_explicit(client, monkeypatch):
    def fail_write(*args):
        raise OSError("Storage unavailable")

    monkeypatch.setattr("lab.reports.save_report", fail_write)
    response = client.post("/api/simulations/bola")
    assert response.status_code == 503
    assert response.json() == {"detail": "Report storage unavailable"}
