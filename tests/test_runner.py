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


def test_report_limit_preserves_existing_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("lab.reports.MAX_REPORTS", 1, raising=False)
    paths = save_report(run_scenario("bola"), tmp_path)
    originals = {path: path.read_bytes() for path in paths}
    with pytest.raises(OSError, match="Report limit reached"):
        save_report(run_scenario("bfla"), tmp_path)
    assert {path: path.read_bytes() for path in paths} == originals
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert len(list(tmp_path.glob("*.md"))) == 1


def test_existing_report_identifier_is_not_overwritten(tmp_path):
    result = run_scenario("bola")
    paths = save_report(result, tmp_path)
    original = {path: path.read_bytes() for path in paths}
    result["passed"] = False
    with pytest.raises(FileExistsError):
        save_report(result, tmp_path)
    assert {path: path.read_bytes() for path in paths} == original


def test_report_write_failure_removes_only_new_partial_files(tmp_path, monkeypatch):
    saved = save_report(run_scenario("bola"), tmp_path)
    original = {path: path.read_bytes() for path in saved}
    result = run_scenario("bfla")
    open_file = type(tmp_path).open

    def failing_open(path, *args, **kwargs):
        if path.name == f"{result['id']}.md":
            raise OSError("Simulated storage failure")
        return open_file(path, *args, **kwargs)

    monkeypatch.setattr(type(tmp_path), "open", failing_open)
    with pytest.raises(OSError, match="Simulated storage failure"):
        save_report(result, tmp_path)
    assert not (tmp_path / f"{result['id']}.json").exists()
    assert {path: path.read_bytes() for path in saved} == original


def test_unknown_evidence_field_names_are_not_exported():
    evidence = _evidence(
        httpx.Response(200, json={"private-key-in-field-name": "value"})
    )
    assert evidence["body"] == {}


def test_concurrent_report_writes_respect_the_limit(tmp_path, monkeypatch):
    monkeypatch.setattr("lab.reports.MAX_REPORTS", 1)
    results = [run_scenario("bola"), run_scenario("bfla")]

    def save(result):
        try:
            save_report(result, tmp_path)
            return True
        except OSError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(save, results))
    assert sorted(outcomes) == [False, True]
    assert len(list(tmp_path.glob("*.json"))) == len(list(tmp_path.glob("*.md"))) == 1
