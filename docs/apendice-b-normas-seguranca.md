# Apêndice B — Normas de Segurança do Sistema

> Acrescentado na certificação (01/09/2026). Duas leituras possíveis:
> **(1) norma-alvo** para evolução multi-tenant/produção; **(2) estado atual**
> do take-home — cada seção traz o mapeamento honesto do que já existe.

## B.1 Identidade — OAuth 2.1 + OpenID Connect com PKCE

| Norma | Detalhe |
|---|---|
| Fluxo | Authorization Code + **PKCE obrigatório** (S256) — sem client secret no browser |
| Tokens | Access **curto** (≤15 min) · **refresh com rotação** (reuso revoga a família) |
| Validação | `iss`/`aud` verificados em toda requisição · JWKS cacheado · algs RS256/ES256 (não `none`, não HS simétrico no client) |
| Sessão do lead (chat) | Continua **pública por capability ULID** (spec §5.4) — OAuth aplica-se a **admin/vendedores** (painel `/handoffs`, purge LGPD) |

**Estado atual:** admin usa `ADMIN_TOKEN` bearer (ADR/Etapa 10 §3) — aceitável
para demo single-operator; a norma OIDC acima é o alvo para multi-usuário.

## B.2 Autorização — RBAC de escopo mínimo (verificado no servidor)

- Papéis: `lead` (capability), `vendedor` (fila/handoffs), `admin` (LGPD/purge/config).
- **Toda checagem no servidor** (nunca só no front); deny-by-default.
- Escopo por endpoint documentado no OpenAPI (`security` por rota) — alvo.

**Atual:** DELETE exige admin (401 sem token — testado no smoke §23/23).

## B.3 Dados — RLS (Row Level Security) por tenant/usuário

- Quando multi-tenant: RLS no Postgres por `tenant_id`/`user_id`;
- App conecta com **usuário de privilégio mínimo** (não superuser) — RLS não
  pode ser bypassável pela role da aplicação;
- Row policies: `USING (tenant_id = current_setting('app.tenant')::uuid)`.

**Atual:** single-tenant demo (InMemoryStore; Postgres real = dívida T-06b) —
a norma entra com o banco real.

## B.4 Perímetro — rate limiting + WAF/CDN

- Rate limit **por IP e por token** (agora: 10 req/min/IP no agent-api — NFR/Etapa 6);
- CDN/WAF na frente da demo (Vercel já fornece para o front); alvo: regras
  anti-DDoS + bot management no agente.
- Timeouts/backpressure já normatizados (Etapa 6 §4.1).

## B.5 Fronteira de dados — DTO como contrato (nunca a entidade do banco)

- **Toda saída HTTP é DTO** do contrato OpenAPI (`QuoteView`, `Timeline`,
  `TurnoResponse`) — a conversa interna (`Conversa`, eventos Bronze) **nunca**
  é exposta diretamente;
- Entrada via `BaseModel` pydantic (422 em payload inválido — smoke ✅);
- PII mascarada **na borda** (spec §3 / NFR-12) — a entidade interna guarda
  Bronze restrito, o DTO só sai mascarado.

## B.6 Checklist OWASP Top 10 — revisado a cada release

| # | Risco | Controle neste sistema | Evidência |
|---|---|---|---|
| A01 Broken Access Control | Capability ULID + admin RBAC + rate limit | smoke 23/23; threat T1-T3 |
| A02 Cryptographic Failures | TLS em trânsito (plataformas); segredos em secret manager | Etapa 10 §3 |
| A03 Injection | pydantic na borda; SQL via ORM parametrizado (alvo PG); prompt injection → price-guard + adversarial 20/20 | evals E3 |
| A04 Insecure Design | Spec-driven + threat model STRIDE 16 ameaças | Etapa 10 §2 |
| A05 Security Misconfiguration | Containers não-root (uid 10001), CORS origem exata, catraca de lint | compose; Etapa 13 |
| A06 Vulnerable Components | pip/npm audit blocker + Trivy + SBOM syft (workflows prontos) | Etapa 15/16 |
| A07 AuthN Failures | (alvo OIDC §B.1); hoje token admin com comparação constante | RB-02 rotação |
| A08 Integrity Failures | Commits assinados por revisão; PR-gate obrigatório; gitleaks no histórico | Etapa 16 §4 |
| A09 Logging Failures | Structured logs c/ correlation_id; sem PII (NFR-12 scan) | Etapa 18 |
| A10 SSRF | Agent-api só fala com allowlist interna (quote-api, LLM) — sem fetch arbitrário | C4 nível 2 |

**Revisão:** este checklist roda no pipeline de release (job `sbom/security`
pronto) e é revalidado a cada release (Apêndice A §A.3).
