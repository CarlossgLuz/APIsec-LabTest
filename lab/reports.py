import json
from pathlib import Path
from uuid import UUID


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
        "Valores internos e campos não previstos são omitidos como [REDACTED]. "
        "Cabeçalhos de autenticação não são registrados.\n"
    )


def save_report(result: dict, output_dir: Path) -> tuple[Path, Path]:
    identifier = str(UUID(result["id"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{identifier}.json"
    markdown_path = output_dir / f"{identifier}.md"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(to_markdown(result), encoding="utf-8")
    return json_path, markdown_path
