# APIsec v2.0

Laboratório de AppSec com FastAPI. Execute simulações de autorização, compare
respostas vulneráveis e protegidas e exporte as evidências em Markdown ou JSON.
Todos os resultados são simulações controladas com dados fictícios.

## Executar localmente

Requisitos: Linux com Python 3.13 ou Docker com Compose v2.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000 para acessar o dashboard. Selecione um cenário,
execute e compare as respostas. Os botões de exportação baixam o resultado atual;
o servidor também salva uma cópia em `reports/`.

A documentação da API fica em http://127.0.0.1:8000/docs. O health check é
`GET /health`.

## Cenários

| Cenário | Operação como Alice | Vulnerável | Protegida |
| --- | --- | --- | --- |
| BOLA — API1:2023 | Ler o documento de Bob | `200` | `404` |
| BFLA — API5:2023 | Excluir o documento de Bob | `204` | `403` |
| BOPLA — API3:2023 | Ler o próprio documento | Expõe `internal_notes` | Omite o campo |

BOLA verifica a permissão sobre o objeto; BFLA, o acesso à operação; BOPLA,
os campos que podem ser devolvidos. A demonstração BOPLA cobre exposição de
propriedades, não alteração indevida de campos.

Cada execução cria duas aplicações com dados novos. A versão vulnerável existe
somente dentro do `TestClient`: suas rotas não são montadas no servidor principal.
Excluir um documento em uma simulação não altera a API principal nem outras execuções.

A API principal mantém dois documentos em memória: 1 de Alice e 2 de Bob.
Alice e Bob leem apenas documentos próprios; Admin lê e exclui qualquer documento.
O modelo de resposta permite apenas `id`, `owner_id`, `title` e `content`, inclusive
para Admin.

Para chamadas diretas, use `Authorization: Bearer <token>`:

| Identidade | Token fictício | ID | Papel |
| --- | --- | --- | --- |
| Alice | `alice-token` | 1 | user |
| Bob | `bob-token` | 2 | user |
| Admin | `admin-token` | 3 | admin |

São valores públicos de laboratório, sem validade como autenticação de produção.
Não exponha esta aplicação à internet. Hosts externos e POSTs de outra origem
são rejeitados; a interface deve ser acessada por `localhost` ou `127.0.0.1`.

## Relatórios e testes

```sh
python -m lab.cli --output-dir reports
python -m lab.cli --scenario bopla --output-dir reports
python -m pytest -v --junitxml=reports/junit.xml
python -m ruff check .
python -m ruff format --check .
python -m bandit -r app lab
```

A CLI retorna código 1 se uma simulação não reproduzir o comportamento esperado.
Cada execução gera um par de arquivos com UUID, referência OWASP, identidade,
operação, respostas, impacto simulado e mitigação. Cabeçalhos de autenticação não
são registrados; valores internos e valores fora dos dados previstos são redigidos.
Não há CVSS, classificação de severidade ou alegação de descoberta real.

O dashboard lê os totais do último `junit.xml`; ele não executa Pytest pelo navegador.
Sem esse arquivo, mostra “Sem registro”. O arquivo representa a última execução
registrada, não uma verificação contínua do código.

`REPORTS_DIR` configura o diretório de saída, com padrão `reports/`. O limite é de
500 pares JSON/Markdown por diretório; ao atingi-lo, novas gravações são recusadas
e a interface retorna `503`. Não há expiração ou exclusão automática. Antes de
liberar espaço, revise e arquive os pares antigos fora desse diretório; no Docker,
copie-os do volume antes de qualquer limpeza manual. A aplicação não remove
evidências existentes.

As gravações são serializadas entre processos e IDs existentes não são
sobrescritos. Uma falha de gravação remove somente os arquivos novos daquela
execução. A interface mostra somente o resultado da sessão atual, sem histórico compartilhado.
Relatórios, caches e arquivos temporários ficam fora do Git.

## Docker Compose

```sh
docker compose config --quiet
docker compose build
docker compose up -d --wait
docker compose ps
```

Acesse http://127.0.0.1:8000. Se a porta estiver ocupada, escolha outra:

```sh
APISEC_PORT=8001 docker compose up -d --wait
```

Nesse caso, acesse http://127.0.0.1:8001 e use o mesmo `APISEC_PORT` nos próximos
comandos de inicialização ou atualização. A publicação permanece no loopback.

O serviço usa usuário sem privilégios, filesystem
somente leitura, volume gravável para relatórios, health check e limites de CPU,
memória, processos e logs. A porta escolhida é publicada apenas em `127.0.0.1`.

```sh
# Gerar relatórios dentro do container
docker compose exec apisec python -m lab.cli --output-dir /app/reports

# Copiar relatórios para o host
mkdir -p reports
docker compose cp apisec:/app/reports/. ./reports

# Parar sem excluir os relatórios
docker compose down
```

Para apresentar o JUnit no dashboard do container, gere-o no host e copie:

```sh
python -m pytest -v --junitxml=reports/junit.xml
docker compose cp reports/junit.xml apisec:/app/reports/junit.xml
```

Use tags distintas para manter a imagem anterior disponível:

```sh
# Registrar a imagem da versão atual antes de atualizar o checkout
APISEC_IMAGE_TAG=previous docker compose build

# Após obter o código da próxima versão
APISEC_IMAGE_TAG=v2 docker compose build
APISEC_IMAGE_TAG=v2 docker compose up -d --no-build --wait

# Rollback para a imagem preservada
APISEC_IMAGE_TAG=previous docker compose up -d --no-build --wait
```

Não use `down -v` se precisar preservar os relatórios. As imagens anteriores
precisam existir localmente para o rollback.

## Pipeline

O [GitHub Actions](.github/workflows/security-tests.yml) executa Ruff, Bandit,
Pytest/JUnit, geração de relatórios, validação do Compose e build da imagem.
Falhas interrompem o job. Os arquivos disponíveis em `reports/` são enviados como
artifacts por 14 dias, inclusive se uma etapa falhar. O workflow roda em push para
`main`, pull request ou acionamento manual; não publica imagem nem faz deploy.

## Preparação para EC2

Implantação manual prevista para uma única instância Linux com Docker Engine,
Compose v2 e Git. Não há provisionamento automatizado.

1. Confira no console a elegibilidade da instância ao Free Tier, a região,
   os créditos e os limites da conta. O selo de elegibilidade não garante custo zero.
2. Use uma instância pequena compatível com a imagem e um volume com espaço para o build.
   Restrinja SSH ao seu IP; mantenha a porta 8000 fechada no Security Group.
3. Copie ou clone uma versão revisada, entre na pasta e execute os comandos de
   build e inicialização do Compose acima.
4. Acesse por túnel SSH, mantendo a publicação restrita ao loopback:

```sh
ssh -L 8000:127.0.0.1:8000 usuario@host-da-instancia
```

Abra http://127.0.0.1:8000 no seu computador. Use o mesmo processo de tags para
atualização e rollback. Esta tarefa não cria instância, IAM, rede ou outros recursos AWS.

A elegibilidade varia conforme a data de criação da conta e as regras vigentes:
[documentação oficial do EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html).

## Estrutura e limites

- `app/`: autenticação, políticas, modelos de resposta e interface Jinja2.
- `lab/`: aplicação vulnerável isolada, executor, relatórios e CLI.
- `tests/`: regressão funcional, cenários de segurança e isolamento.
- `reports/`: resultados locais e JUnit, fora do Git.

Não há banco de dados, scanner de URLs ou autenticação de produção. Os dados da
API principal são locais ao processo e reiniciam com o servidor; use um único worker.
As simulações sempre partem de cópias novas.

Validação local: 86 testes aprovados em ordem normal, inversa e aleatória;
Ruff, Bandit e `pip check` aprovados. Imagem construída
e Compose com health check aprovado no Docker Engine 29.9.0 / Compose 5.6.0.
Build limpo, dashboard desktop/mobile, cenários via HTTP e CLI, exportações,
exclusões repetidas e encerramento controlado verificados em projeto isolado
com `APISEC_PORT=8002`. Containers e volumes anteriores foram preservados.
A base usa digest fixo e as dependências existentes, incluindo transitivas, têm
versões exatas. O container e o ambiente local usam os mesmos 20 pacotes runtime.

Starlette emite um aviso de depreciação do TestClient com httpx. Os cenários passam;
nenhuma validação foi desativada para ocultar esse aviso. As verificações locais
não comprovam uma execução remota do GitHub Actions.

Se o terminal do VS Code estiver em Flatpak, o Docker pode estar disponível apenas
no sistema hospedeiro. Execute os comandos em um terminal do host.

Referências: [OWASP API Security 2023](https://owasp.org/API-Security/editions/2023/en/0x00-header/)
e [Compose Specification](https://docs.docker.com/reference/compose-file/services/).
