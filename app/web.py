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
def simulate(scenario: str, request: Request):
    from lab.reports import save_report, to_markdown
    from lab.runner import SCENARIOS, run_scenario

    origin = request.headers.get("origin")
    expected_origin = f"{request.url.scheme}://{request.url.netloc}"
    if (origin is not None and origin != expected_origin) or request.headers.get(
        "sec-fetch-site"
    ) == "cross-site":
        raise HTTPException(status_code=403, detail="Cross-origin execution denied")
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
        if root.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Unsupported root")
        suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        if not suites:
            raise ValueError("Missing suites")
        counts = dict.fromkeys(("tests", "failures", "errors", "skipped"), 0)
        for suite in suites:
            values = {}
            for key in counts:
                value = suite.get(key, "")
                if not value.isascii() or not value.isdecimal():
                    raise ValueError("Invalid counts")
                values[key] = int(value)
            if (
                sum(values[key] for key in ("failures", "errors", "skipped"))
                > values["tests"]
            ):
                raise ValueError("Inconsistent counts")
            for key in counts:
                counts[key] += values[key]
        return {"available": True, **counts, "source": "junit.xml"}
    except (OSError, ElementTree.ParseError, DefusedXmlException, ValueError):
        return {"available": False}
