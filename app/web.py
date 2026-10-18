import os
from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/api/scenarios")
def scenarios():
    from lab.runner import SCENARIOS

    return [{"id": name, **details} for name, details in SCENARIOS.items()]


@router.post("/api/simulations/{scenario}")
def simulate(scenario: str):
    from lab.reports import save_report, to_markdown
    from lab.runner import SCENARIOS, run_scenario

    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    result = run_scenario(scenario)
    try:
        save_report(result, Path(os.environ.get("REPORTS_DIR", "reports")))
    except OSError as exc:
        raise HTTPException(
            status_code=503, detail="Report storage unavailable"
        ) from exc
    return {"result": result, "markdown": to_markdown(result)}


@router.get("/api/test-status")
def test_status():
    path = Path(os.environ.get("REPORTS_DIR", "reports")) / "junit.xml"
    try:
        with path.open("rb") as report:
            data = report.read(2_000_001)
        if (
            len(data) > 2_000_000
            or b"<!DOCTYPE" in data.upper()
            or b"<!ENTITY" in data.upper()
        ):
            raise ValueError("Unsupported XML")
        root = ElementTree.fromstring(data)
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        if not suites:
            raise ValueError("Missing suites")
        counts = {
            key: sum(int(suite.get(key, "0")) for suite in suites)
            for key in ("tests", "failures", "errors", "skipped")
        }
        if any(value < 0 for value in counts.values()):
            raise ValueError("Invalid counts")
        return {"available": True, **counts, "source": "junit.xml"}
    except (OSError, ElementTree.ParseError, DefusedXmlException, ValueError):
        return {"available": False}
