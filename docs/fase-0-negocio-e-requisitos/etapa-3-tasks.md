# Etapa 3 — Tasks (fluxo Spec Kit: spec → plan → tasks)

> Decomposição da spec em tarefas implementáveis. Cada task segue o template
> (`etapa-3-template-ticket.md`), é TDD-first e referencia a seção exata da
> spec. **Ordem = ordem sugerida de execução** (dependências explícitas).
>
> As tasks de código só iniciam após as fases 1-2 do guia (ADRs, contratos,
> repo) — a ordem aqui respeita o processo.

## Épico A — Fundações (pós Etapas 4-9)

**T-01 — Scaffold do monorepo**
Contexto: criar a estrutura de diretórios e configs base do repo de entrega.
Spec: §9 (ambiente) · Fase 2 do guia.
Entregáveis: `apps/web` (Next) · `services/agent-api` (FastAPI) · `quote-service` (cópia intocada) · `docs` · `ai-logs` · compose + Makefile.
Restrições: **nenhum** arquivo do `quote-service` alterado; segredos fora.
DoD: `make dev` sobe postgres + quote-api; `make test` roda vazio verde.
Depende de: Etapa 9.

**T-02 — Módulo `masking.py` (puro)**
Contexto: base de tudo (LLM, logs, Silver) — spec §3 exato.
Testes primeiro: 5 regex × casos do `sample.jsonl` (CPF, e-mail, telefone,
placa, CEP; ordem de aplicação; idempotência — mascarar 2× = mesmo resultado).
DoD: cobertura 100% do módulo; propriedade "nunca retorna PII crua" em fuzz simples.
Depende de: T-01.

**T-03 — Cliente `/quote` + resiliência (ACL)**
Contexto: timeout/backoff/breaker da spec §2 — o coração do desafio.
Testes primeiro (relógio fake): 3 tentativas com backoff 500/1000+jitter;
timeout 3s; 5xx/timeout contam, 422/400 não; breaker 5/30/2; simulação 1.000
cotações com p=0.30 → sucesso ≥ 97% (NFR-04); contratado contra **mock** httpx.
DoD: cobertura ≥ 90%; parâmetros lidos de env com defaults assertados.
Depende de: T-01.

## Épico B — Motor da conversa

**T-04 — Máquina de estados**
Contexto: spec §1 completa — tabela de transições + 4 invariantes.
Testes primeiro: cada linha da tabela 1.3 como caso; invariantes 1-4 como
testes de propriedade (nunca apresenta valor sem `QUOTE_OK`; `HANDOFF`
absorvente; `CORRIGE` substitui; terminais mudos).
DoD: módulo puro sem I/O; cobertura ≥ 90%.
Depende de: T-01.

**T-05 — Camada LLM (client + pós-validação)**
Contexto: spec §4 — 1 call/turno, JSON mode, validação de campos (§4.4),
guardrail de preço (§4.3).
Testes primeiro: contra LLM **fake** determinístico (respostas fixture);
viol #1 regenera, viol #2 fallback canônico; evento `price_guard_violation`
logado; campos inválidos descartados (idade 200, ano 2030, CEP "abc").
DoD: NFR-09 verificável sem rede.
Depende de: T-02, T-04.

**T-06 — Persistência (Postgres) + eventos**
Contexto: spec §5.2 — tabelas `conversations`, `events`, `handoffs`; migração v1.
Testes: repositório contra Postgres de teste no compose; reconstituição de
timeline por `conversation_id` ordenada por `seq`.
DoD: migração roda idempotente; `DELETE /conversations/{id}` apaga cascata (LGPD).
Depende de: T-04. (Detalhe do schema: Etapa 6.)

**T-07 — API HTTP (endpoints §5.4)**
Contexto: rotas da spec §5.4 com problem+json, ULID, health com status do legado.
Testes: contrato por httpx AsyncClient app-in-memory; happy C1 como teste de
integração ponta a ponta com legado mockado estável.
DoD: OpenAPI gerada servida em `/openapi.json` (input da Etapa 5).
Depende de: T-03, T-05, T-06.

## Épico C — Dados & Evals

**T-08 — `build_silver.py`**
Contexto: spec §7 — comando único Bronze→Silver + relatório.
Testes: roda sobre `sample.jsonl`→parquet fixture; 100% PII mascarada;
ordenado por `message_index`; `marca/modelo/ano` extraídos (dicionário fechado).
DoD: relatório imprime % masking = 100% e % veículo normalizado.
Depende de: T-02.

**T-09 — Evals de extração e handoff**
Contexto: NFR-10/NFR-11 — 200 conversas amostradas do Silver rotuladas.
Entregáveis: `evals/` com runner; gate ≥ 90% extração · ≥ 95% handoff.
Depende de: T-05, T-08.

**T-10 — Suite adversarial (20 ataques)**
Contexto: spec §10 literal — 20 casos, 0 tolerância (NFR-14).
Depende de: T-05. (Roda em CI: Etapa 13.)

## Épico D — Front & Demo

**T-11 — Chat `/`** (spec §8: componentes, estados, mobile-first, localStorage só com id).
Testes: componentes (Vitest/RTL) + Lighthouse ≥ 90 no CI. Depende de: T-07.
**T-12 — Fila `/handoffs`** (tabela motivo/espera + conversa legível mascarada). Depende de: T-07, T-11.
**T-13 — Export de conversa** (JSON+MD, PII mascarada) — botão no chat. Depende de: T-07, T-11.

## Épico E — Release & Entrega

**T-14 — CI completo** (lint, testes, gates NFR-09/12/14, coverage ≥ 90%, gitleaks) — Etapa 13.
**T-15 — Deploy demo** (Railway: agent-api+quote-api+Postgres · Vercel: front · região GRU) — Etapa 14.
**T-16 — Bateria TRA + log de execução** (C1-C6 rodando na demo; export do C1 como artefato final da entrega).
**T-17 — `ai-logs/` sanitizado + RETRO.md** (Etapa 18) — fecho da entrega.

## Dependências (grafo)

```
T-01 ─┬─ T-02 ─┬─ T-08 ── T-09
      ├─ T-03 ─┤
      ├─ T-04 ─┼─ T-05 ── T-10
      │        └─ T-06 ── T-07 ─┬─ T-11 ─ T-12
      │                         │        └─ T-13
      └─────────────────────────┴─ T-14 ─ T-15 ─ T-16 ─ T-17
```

## Regra de execução (TDD)

1. Ticket aberto pelo template · 2. teste vermelho · 3. implementação mínima ·
4. verde · 5. refatora · 6. DoD marcada · 7. PR pequeno referenciando spec §.
