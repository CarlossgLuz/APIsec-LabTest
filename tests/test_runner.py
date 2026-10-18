import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx
import pytest

from app.main import documents
from lab.cli import main
from lab.reports import save_report, to_markdown
from lab.runner import SCENARIOS, _evidence, run_scenario


@pytest.mark.parametrize("name", SCENARIOS)
def test_scenarios_capture_expected_controlled_results(name):
    result = run_scenario(name)
    assert result["scenario"] == name
    assert result["simulation"] is True
    assert result["passed"] is True
    encoded = json.dumps(result)
    assert "alice-token" not in encoded
    assert "Bearer" not in encoded
    assert "Synthetic internal review" not in encoded
    assert "cvss" not in encoded.lower()
    if name == "bopla":
        assert result["vulnerable"]["body"]["internal_notes"] == "[REDACTED]"
        assert "internal_notes" not in result["protected"]["body"]


def test_concurrent_runs_do_not_mutate_main_application():
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(run_scenario, ["bfla", "bola", "bfla", "bopla"] * 2)
        )
    assert all(result["passed"] for result in results)
    assert len({result["id"] for result in results}) == len(results)
    assert 2 in documents


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError, match="Unknown scenario"):
        run_scenario("https://example.com")


def test_evidence_omits_unexpected_values_and_authentication_fields():
    response = httpx.Response(
        200,
        json={
            "id": 1,
            "title": "private value",
            "authorization": "Bearer secret",
            "internal_notes": "private note",
        },
    )
    encoded = json.dumps(_evidence(response))
    assert "private value" not in encoded
    assert "Bearer secret" not in encoded
    assert "private note" not in encoded


def test_report_exports_match_the_run(tmp_path):
    result = run_scenario("bopla")
    json_path, markdown_path = save_report(result, tmp_path)
    assert json.loads(json_path.read_text()) == result
    markdown = markdown_path.read_text()
    assert markdown == to_markdown(result)
    assert "Simulação controlada" in markdown
    assert result["owasp"] in markdown
    assert "Synthetic internal review" not in markdown
    assert "alice-token" not in markdown


def test_report_identifier_cannot_escape_output_directory(tmp_path):
    result = {"id": "../outside"}
    with pytest.raises(ValueError):
        save_report(result, tmp_path)


def test_cli_generates_all_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["lab.cli", "--output-dir", str(tmp_path)])
    assert main() == 0
    assert len(list(tmp_path.glob("*.json"))) == 3
    assert len(list(tmp_path.glob("*.md"))) == 3


def test_cli_returns_failure_when_expectation_is_not_met(tmp_path, monkeypatch):
    result = run_scenario("bola")
    result.update(passed=False, id=str(uuid4()))
    monkeypatch.setattr("lab.cli.run_scenario", lambda name: result)
    monkeypatch.setattr(
        "sys.argv", ["lab.cli", "--scenario", "bola", "--output-dir", str(tmp_path)]
    )
    assert main() == 1
