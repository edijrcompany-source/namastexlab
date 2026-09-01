# Etapa 10 — Segurança e Threat Modeling

> Fase 1 (fecha a fase) · STRIDE em uma página, no design — antes do código.
> Consolida: hotspots H6 (injeção) e H7 (PII) da Fase 0 · LGPD (Etapa 2) ·
> resiliência e rate limit (Etapa 6) · price-guard (spec §4.3) · suite
> adversarial de 20 ataques (spec §10).

---

## 1. Superfícies de ataque

```
                    Internet
 ┌──────────┐  HTTPS │  ┌──────────────┐    rede interna Railway/compose
 │ Vercel   ├────────┼─▶│ S1 agent-api ├───────┬─────────┬─────────┐
 │ S3 front │  CORS  │  │  (público)   │   S4  │     S6  │    S5   │
 └──────────┘        │  │ S2 /admin/*  │ quote-│ Postgres│  LLM API│
                     │  └──────────────┘  api  │         │ provider│
                     │                    (int)│  (int)  │  (ext)  │
   S7 repo público (GitHub): código, dataset Bronze, ai-logs/, docs
   S8 worker retry_quote (interno, loop assíncrono)
```

## 2. STRIDE (uma página — ameaça → mitigação → residual)

| # | Superfície | Categoria | Ameaça | Mitigação | Residual |
|---|---|---|---|---|---|
| T1 | S1 | **S**poofing | Terceiro acessa conversa alheia (sabe/adivinha ULID) | ULID = **capability** (80 bits aleatórios, não enumerável); sem endpoint de listagem pública; timeline só por ULID exato | ✅ aceito (demo) — anotado |
| T2 | S1 | **S**poofing | Flood de mensagens (bot) | Rate limit **10 req/min/IP** + `Retry-After` (Etapa 6) + `text` ≤ 4.000 chars | ✅ baixo |
| T3 | S2 | **S**poofing | Alguém chama `DELETE`/`/admin/purge`/fila | `ADMIN_TOKEN` bearer (≥32 chars, comparação constant-time); só S2 exige token | ✅ baixo |
| T4 | S1 | **T**ampering | Payload malformado/inesperado | pydantic valida **contrato** (Etapa 5); mídia só marcador; campos com regex/regras (spec §4.4) | ✅ baixo |
| T5 | S1/S5 | **T**ampering | **Injeção de prompt (H6)** — lead manipula o Agente ("me dá 50% off", "ignore regras") | 3 camadas: ① prompt com instruções invioláveis e **zero ferramentas**; ② **código**: price-guard pós-LLM + validação de campos; ③ **processo**: 20 ataques em CI (NFR-14, 0 tolerância). *Superfície de dano mínima: o Agente NÃO TEM capacidade de desconto/emissão — ataque "bem-sucedido" não encontra o que comprometer* | ✅ baixo (monitorado por eval) |
| T6 | S5 | **T**ampering | Resposta do LLM corrompida/alucinada | Saída = **dado não confiável**: JSON schema validado; preço só passa se bater com cotação real (`quote_id`) | ✅ baixo |
| T7 | Todos | **R**epudiation | "Não fui eu / não aconteceu" | Event store append-only + `correlation_id` por turno (Etapa 6/8) — trilha auditável | ✅ |
| T8 | S1/S7 | **I**nformation disclosure | **PII vazada (H7)** em resposta/log/export | Masking §3 spec em **toda saída** (NFR-12 com scan por regex no CI); `MASKING_STRICT=true` (falha em vez de logar cru); PII mascarada **antes** do LLM | ✅ baixo |
| T9 | S5 | **I**nfo disclosure | PII ingerida pelo provider de LLM | Tokens `[CPF_1]` no lugar de PII; provider com retenção zero (quando houver opção); risco documentado no LGPD (Etapa 2 §3.2-3) | 🟡 aceito (mitigado) |
| T10 | S1 | **I**nfo disclosure | Stack trace/erro técnico exposto | problem+json sem internals (Etapa 6 §1.2) | ✅ |
| T11 | S7 | **I**nfo disclosure | **Segredo vazado no repo — inclusive nos `ai-logs/`** (exports de IA!) | **gitleaks no CI varrendo repo TODO (histórico) + `ai-logs/` + docs** (NFR-13); sanitização manual dos exports antes do commit (README do desafio exige) | ✅ baixo |
| T12 | S1/S5 | **D**oS | turno caro em loop; bomba de tokens LLM | Timeout 15s + retry 1 (LLM) · `max_tokens=500` · budget NFR-15 ≤ US$ 5/mês monitorado | ✅ |
| T13 | S4/S6 | **D**oS / **T**ampering | Ataque via rede interna | Rede privada Railway (quote-api/Postgres **não expostos publicamente** — domínio interno); TLS interno | ✅ |
| T14 | S8 | **E**levation | Worker executa algo fora do escopo | Worker só faz `retry_quote` (sem input externo); transições restritas à máquina de estados (invariantes testadas) | ✅ |
| T15 | S3 | **T**ampering | XSS via texto do lead/chat | React escapa por padrão (sem `dangerouslySetInnerHTML` — regra eslint); security headers no Next (CSP básica, X-Content-Type-Options, Referrer-Policy) | ✅ |
| T16 | S3→S1 | **S**poofing | CORS aberto | CORS **origem exata** do domínio Vercel + `localhost` em dev — nunca `*` | ✅ |

## 3. Segredos — onde moram, rotação, scan

| Segredo | Onde mora | Front precisa? | Rotação | Scan |
|---|---|---|---|---|
| `LLM_API_KEY` | Railway env (somente agent-api) | ❌ **nunca** na Vercel | Procedimento 90 dias (UI Railway → novo valor → redeploy) | gitleaks + semgrep no-secrets |
| `DATABASE_URL` | Railway env (internal) | ❌ | Rotação via plataforma | gitleaks |
| `ADMIN_TOKEN` | Railway env | ❌ | Idem | gitleaks |
| Dev local | `.env` (já coberto pelo `.gitignore` do desafio: `.env*`, `*.key`, `*.pem`) | — | — | gitleaks |

**Decisão (inline):** Secrets Manager da plataforma (Railway) em vez de Vault — 3 segredos, 1 serviço, time de 1; Vault agregaria operação sem ganho de segurança neste porte. Gatilho de revisão: multi-ambiente com times distintos. **Rotação testada** como procedimento documentado (o guia pede rotação — registramos o runbook, executar 1× na entrega).

## 4. Autenticação/autorização entre serviços

| Comunicação | Auth | Justificativa |
|---|---|---|
| Vercel → agent-api (S1) | Nenhuma de usuário (demo aberta) + **capability ULID** + rate limit | Lead não cria conta; conversa é o recurso |
| → S2 (admin) | `ADMIN_TOKEN` (bearer, constant-time) | Pontual: DELETE LGPD, purge, fila |
| agent-api → quote-api (S4) | Nenhuma — **rede privada** | Não existe expor o legado à internet (Railway internal domain) |
| agent-api → LLM (S5) | `LLM_API_KEY` (header do provider) | Padrão do provider |
| agent-api → Postgres (S6) | Usuário/senha internos + TLS | Gerenciado pela plataforma |

## 5. Scans obrigatórios (porta de entrada do CI — Etapa 16)

| Scan | Ferramenta | Escopo | Quando | Gate |
|---|---|---|---|---|
| Segredos | **gitleaks** | Repo inteiro **+ histórico** + `ai-logs/` + `docs/` | Cada PR + nightly | **blocker** |
| SAST | **CodeQL** (grátis em repo público): python + javascript | `services/agent-api`, `apps/web` | Cada PR | blocker em error |
| SAST custom | **semgrep** 3 regras: segredo hardcoded (padrões BR: CPF/token), SQL por f-string, `dangerouslySetInnerHTML` | py + ts | cada PR | blocker |
| Dependências (S6 do repo) | **pip-audit** (uv.lock/requirements) + **npm audit --audit-level=high** | back + front | cada PR + weekly | **CVE crítica = blocker** (guia) |
| Freshness | Dependabot/renovate | weekly | — | PR automático |
| PII em saída | teste regex NFR-12 (Etapa 2) | logs/exports | cada PR | blocker |
| Injeção | suite adversarial 20 ataques (spec §10) | agent-api c/ legado mock | cada PR | **0/20 blocker** |

**OWASP ASVS:** alvo **Level 1** (demo sem dados reais). Controles selecionados mapeados: V2 (capability + admin token), V3 (session N/A), V4 (controle de acesso por ULID + rate limit), V5 (pydantic + escapamento), V7 (erros sem stack), V8 (logs com correlation, sem PII), V14 (CORS restrito + headers).

**OWASP Top 10 p/ LLM (mapa rápido):** LLM01 injeção → T5 · LLM02 divulgação sensível → T8/T9 · LLM03 supply chain → tabela de scans · LLM06 dados pessoais → LGPD Etapa 2 · LLM09 excesso de confiança (preço alucinado) → price-guard + carência sempre da API.

## 6. ✅ Portão de validação da Etapa 10

| Critério | Status |
|---|---|
| Scan de segredos passa limpo | 🟡 gitleaks definido como **blocker** no CI (Etapa 16) + sanitização dos `ai-logs/` antes do commit — hoje: repo de docs sem segredo (verificado manualmente: nenhum secret nos artefatos) |
| Ameaças mapeadas têm mitigação | ✅ 16 ameaças STRIDE, todas com mitigação e residual declarado (2 aceitos-documentados: T1 capability, T9 provider LLM) |
| Dependências sem CVE crítica conhecida | 🟡 policy blocker (pip-audit + npm audit); verificação de fato quando lockfiles existirem (Épico A) — hoje a única dependência existente (`quote-service/uv.lock`, do desafio) será auditada no primeiro pipeline run |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Fase 1 fechada; Etapa 11 liberada)*
