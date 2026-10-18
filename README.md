# APIsec-LabTest

Laboratório local de AppSec com FastAPI. Bloco 1: autenticação demonstrativa,
autorização e documentos sintéticos em memória.

## Executar

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

A documentação interativa está em http://127.0.0.1:8000/docs.

## Autenticação e permissões

Use `Authorization: Bearer <token>` com estes valores públicos e fictícios:

| Pessoa | Token de laboratório | ID | Papel |
| --- | --- | --- | --- |
| Alice | `alice-token` | 1 | user |
| Bob | `bob-token` | 2 | user |
| Admin | `admin-token` | 3 | admin |

O documento 1 pertence a Alice; o documento 2, a Bob.
Alice e Bob leem apenas documentos próprios. Admin lê e exclui qualquer documento.
Leitura de documento alheio e inexistente retorna o mesmo `404`.
Exclusão por usuário comum retorna `403`; exclusão por Admin retorna `204` sem corpo.
Documento inexistente retorna `404` para Admin. Token ausente ou inválido retorna `401`.
`GET /health` é público.

```sh
curl -i -H 'Authorization: Bearer alice-token' http://127.0.0.1:8000/documents/1
curl -i -H 'Authorization: Bearer alice-token' http://127.0.0.1:8000/documents/2
curl -i -X DELETE -H 'Authorization: Bearer admin-token' http://127.0.0.1:8000/documents/2
```

## Testes

```sh
python -m pytest -v
```

Os testes restauram o estado em memória após cada caso, inclusive quando falham.
Há cobertura de autenticação, isolamento entre proprietários, privilégios de Admin,
exclusão, documento inexistente e health check.

## Limites e próximos blocos

Tokens fixos são somente demonstrativos e não servem para produção.
Os documentos são locais ao processo e reiniciam com o servidor; execute um único worker.
Não há frontend, banco de dados ou JWT. Simulações ofensivas BOLA/BFLA e GitHub Actions
ficam para os próximos blocos.

Registro da entrega e validação: [docs/bloco-1.md](docs/bloco-1.md).
