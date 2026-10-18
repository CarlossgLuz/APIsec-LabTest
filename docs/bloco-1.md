# Bloco 1 — API funcional

## Passo a passo

1. Conferidos branch `main`, remoto e alterações locais. Os três testes existentes passaram.
2. Implementada autenticação com três tokens públicos fictícios e identidade com ID/papel.
3. Centralizadas as políticas de leitura por proprietário/Admin e exclusão apenas por Admin.
4. Implementados GET/DELETE com dois documentos sintéticos em memória.
5. Atualizado o erro de token inválido e adicionados testes de autorização e exclusão.
6. Adicionada fixture que restaura os documentos após cada teste.
7. Documentada a execução local e registradas as versões instaladas das dependências.

## Evidência

`python -m pytest -v`: 26 testes aprovados, incluindo os três originais.
O health check permanece público. Exclusão bem-sucedida retorna corpo vazio.

## Escopo e recuperação

Somente Bloco 1. O workflow local preexistente não foi incluído na entrega.
Tokens demonstrativos não constituem autenticação de produção.
O estado não é persistido nem compartilhado entre processos; reiniciar repõe os documentos.
Para rollback de código, reverter os commits desta entrega com `git revert`, sem apagar trabalho local.
