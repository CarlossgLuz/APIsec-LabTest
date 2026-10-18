import fcntl
import json
from pathlib import Path
from uuid import UUID

MAX_REPORTS = 500


def to_markdown(result: dict) -> str:
    evidence = json.dumps(
        {"vulnerable": result["vulnerable"], "protected": result["protected"]},
        ensure_ascii=False,
        indent=2,
    )
    status = "Confirmado" if result["passed"] else "Resultado inesperado"
    return (
        f"# {result['title']}\n\n"
        "Simulação controlada com dados fictícios. "
        "Não é uma descoberta em sistema real.\n\n"
        f"- Referência OWASP: {result['owasp']}\n"
        f"- Execução: {result['id']}\n"
        f"- Data UTC: {result['generated_at']}\n"
        f"- Identidade: {result['user']}\n"
        f"- Operação: `{result['operation']}`\n"
        f"- Resultado: {status}\n\n"
        f"## Evidências\n\n```json\n{evidence}\n```\n\n"
        f"## Impacto simulado\n\n{result['impact']}\n\n"
        f"## Mitigação\n\n{result['mitigation']}\n\n"
        "Campos não previstos são omitidos; valores internos usam [REDACTED]. "
        "Cabeçalhos de autenticação não são registrados.\n"
    )


def save_report(result: dict, output_dir: Path) -> tuple[Path, Path]:
    identifier = str(UUID(result["id"]))
    payloads = {
        output_dir / f"{identifier}.json": (
            json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        ),
        output_dir / f"{identifier}.md": to_markdown(result),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / ".report.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if sum(1 for _ in output_dir.glob("*.json")) >= MAX_REPORTS:
            raise OSError("Report limit reached; archive existing reports first")
        created = []
        try:
            for path, content in payloads.items():
                with path.open("x", encoding="utf-8") as report:
                    created.append(path)
                    report.write(content)
        except OSError:
            for path in created:
                path.unlink(missing_ok=True)
            raise
    return tuple(payloads)
