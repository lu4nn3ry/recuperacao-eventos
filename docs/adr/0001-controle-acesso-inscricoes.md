# ADR 0001 — Controle de acesso na listagem de inscrições

- **Status:** Aceito
- **Data:** 2026-02-14
- **Contexto:** Revisão de segurança semanal (issue #1)

## Contexto

O endpoint `GET /eventos/<id>/inscricoes` retornava nome e e-mail de todos
os participantes sem qualquer autenticação, expondo dados pessoais (LGPD)
a qualquer pessoa com acesso à API — classificado como **ALTO (9/10)**.

## Decisão

Exigir autenticação por chave de administrador no endpoint:

1. A rota só responde com o header `X-Admin-Key` válido.
2. A chave é comparada com a variável de ambiente `ADMIN_API_KEY` usando
   `hmac.compare_digest` (proteção contra timing attacks).
3. **Fail-closed:** sem `ADMIN_API_KEY` configurada, nenhuma requisição é
   autorizada — o endpoint falha seguro por padrão.
4. Os demais endpoints (listar eventos, lotação, inscrição) permanecem
   públicos, pois não expõem dados pessoais.

## Consequências

- **Positivas:** dados de participantes protegidos; comportamento
  fail-closed; testes automatizados (`tests/test_app.py`) cobrem os quatro
  cenários (sem chave configurada, sem header, chave errada, chave certa).
- **Negativas:** administradores precisam configurar `ADMIN_API_KEY` no
  ambiente para consultar inscrições.
- **Futuro:** para produção com múltiplos administradores, migrar para
  autenticação com tokens de sessão e níveis de papel (roles).
