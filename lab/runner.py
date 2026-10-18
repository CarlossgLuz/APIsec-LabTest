from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.data import create_documents
from app.main import create_app
from lab.vulnerable_app import create_vulnerable_app

SCENARIOS = {
    "bola": {
        "title": "BOLA — acesso a documento de outro usuário",
        "owasp": "API1:2023 — Broken Object Level Authorization",
        "description": "Alice tenta ler o documento de Bob alterando o ID do recurso.",
        "operation": "GET /documents/2",
        "user": "Alice",
        "impact": "Leitura indevida de dados de outro proprietário.",
        "mitigation": (
            "Validar a propriedade do documento ou o papel administrativo "
            "antes da leitura."
        ),
    },
    "bfla": {
        "title": "BFLA — exclusão sem privilégio administrativo",
        "owasp": "API5:2023 — Broken Function Level Authorization",
        "description": "Alice tenta executar uma operação reservada ao Admin.",
        "operation": "DELETE /documents/2",
        "user": "Alice",
        "impact": "Exclusão indevida por usuário sem permissão administrativa.",
        "mitigation": "Exigir o papel administrativo antes de permitir exclusões.",
    },
    "bopla": {
        "title": "BOPLA — exposição de propriedade interna",
        "owasp": "API3:2023 — Broken Object Property Level Authorization",
        "description": "Alice consulta seu documento e verifica os campos devolvidos.",
        "operation": "GET /documents/1",
        "user": "Alice",
        "impact": "Exposição de propriedades internas mesmo em um objeto autorizado.",
        "mitigation": (
            "Definir um modelo de resposta com uma lista explícita de campos públicos."
        ),
    },
}


def _evidence(response):
    if not response.content:
        body = None
    else:
        raw = response.json()
        seed = create_documents().get(raw.get("id"), {})
        body = {}
        for key, value in raw.items():
            if key not in {
                "id",
                "owner_id",
                "title",
                "content",
                "detail",
                "internal_notes",
            }:
                continue
            if key in {"id", "owner_id", "title", "content"} and value == seed.get(key):
                body[key] = value
            elif key == "detail" and value in {
                "Document not found",
                "Permission denied",
            }:
                body[key] = value
            else:
                body[key] = "[REDACTED]"
    return {"status_code": response.status_code, "body": body}


def run_scenario(name: str) -> dict:
    if name not in SCENARIOS:
        raise ValueError("Unknown scenario")
    scenario = SCENARIOS[name]
    method, path = scenario["operation"].split(" ", 1)
    with (
        TestClient(create_vulnerable_app()) as vulnerable,
        TestClient(create_app(include_ui=False)) as protected,
    ):
        headers = {"Authorization": "Bearer alice-token"}
        exposed = vulnerable.request(method, path, headers=headers)
        corrected = protected.request(method, path, headers=headers)
        exposed_body = exposed.json() if exposed.content else None
        corrected_body = corrected.json() if corrected.content else None
        if name == "bola":
            passed = exposed.status_code == 200 and corrected.status_code == 404
        elif name == "bfla":
            passed = (
                exposed.status_code == 204
                and corrected.status_code == 403
                and 2 not in vulnerable.app.state.documents
                and 2 in protected.app.state.documents
            )
        else:
            passed = (
                exposed.status_code == corrected.status_code == 200
                and "internal_notes" in exposed_body
                and "internal_notes" not in corrected_body
            )
    return {
        "id": str(uuid4()),
        "scenario": name,
        **scenario,
        "simulation": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "vulnerable": _evidence(exposed),
        "protected": _evidence(corrected),
        "passed": passed,
    }
