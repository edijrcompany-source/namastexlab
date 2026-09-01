# Etapa 19 — Avaliação Contínua de IA (evals)

> Fase 4 · Teste tradicional não cobre comportamento de agente/LLM.
> **Casos dourados versionados com o código, cada chamada de modelo rastreada,
> FinOps de token com alerta de orçamento — e mudança de prompt passa pela
> suíte como mudança de código.**

---

## 1. A suíte — 5 evals (todos derivados do que já especificamos)

| # | Eval | Base | Gate | Onde roda |
|---|---|---|---|---|
| **E1** | Extração de qualificação | 200 amostras **Silver** rotuladas (seed: `golden/extraction.seed.jsonl`, cresce no repo) | ≥90% campo-correto (NFR-10) | PR (FakeLLM p/ contrato) + noturno (LLM real) |
| **E2** | Decisão de handoff | casos rotulados por motivo (`golden/handoff.seed.jsonl` — os 6 motivos) | ≥95% (NFR-11) | idem |
| **E3** | **Adversarial** | os 20 ataques da spec §10 em formato máquina (`golden/adversarial.jsonl`) | **0/20 violações — blocker** (NFR-14) | idem |
| **E4** | Price-guard | respostas vs cotações da API (mock determinístico) | **0 preços sem origem — blocker** (NFR-09) | PR |
| **E5** | Golden comportamental ponta a ponta | **C1-C6** (spec §11) como casos dourados, com `QUOTE_SEED=42` | 6/6 passam | noturno + pré-release (E2E da Etapa 14) |
| (métrica) | **TRA** (métrica norte) | bateria simulada de conversas elegíveis | ≥70% (SLO-3) | noturno → alerta `TRAReprovada` |

**Runner — decisão (inline, coerente com ADR-0004):** runner **próprio mínimo**
(pytest marker `@evals` + `make evals`) — integra com FakeLLM no CI offline,
mede exatamente nossos gates e não adiciona serviço. *promptfoo/DeepEval*
registrados como alternativas com gatilho: suíte >200 casos ou necessidade de
harness com UI de comparação. **RAGAS: N/A justificado** — o agente não tem
RAG (o dataset é fonte de evals/few-shot, não base de recuperação).

## 2. Datasets dourados — versionados junto com o código (`evals/golden/`)

```
evals/golden/
├── extraction.seed.jsonl    # seed inicial: textos Silver (PII pré-mascarada §3) + expected
├── handoff.seed.jsonl       # casos por motivo (os 6 da spec §5.3)
└── adversarial.jsonl        # os 20 ataques da spec §10 — must / must_not
```

Formato (um caso por linha): `{id, estado, user_input, expected: {…}}`.
Regras: **golden é código** (PR + revisão como qualquer código); caso dourado
que falha por ambiência vira issue de spec primeiro (AGENTS.md); entradas
**sempre** da Silver (PII mascarada — nunca Bronze).

## 3. Prompt é código — mudança passa pela suíte

- Prompts vivem em `prompts/` versionados com semver próprio (detalhe na Etapa 20).
- **CI path-trigger (bloqueante):** PR que toca `prompts/**` roda o job
  `evals-prompts` com **LLM real** (validar prompt com FakeLLM não prova nada) —
  E1+E2+E3 contra o golden; regressão = PR vermelho.
- Noturno roda a suíte completa com LLM real contra a main — degradação
  silenciosa de modelo/provedor é detectada em ≤24h.

## 4. FinOps de token — a nova conta de infraestrutura

**Cada chamada de modelo rastreada** (no span OTel `llm.completion` + log
estruturado + métricas):

```json
{ "conversation_id": "01J8…", "turno_seq": 7, "model": "gpt-4o-mini",
  "prompt_tokens": 1830, "completion_tokens": 210,
  "cost_usd": 0.000573, "latency_ms": 2140, "prompt_version": "system_v1" }
```

| Controle | Regra | Alerta (adicionados a `observability/alerts.yml`) |
|---|---|---|
| Custo por conversa | média 7d **> US$ 0,10** (NFR-15) | 🟡 `CustoConversaAcima` → RB-05 (revisar prompt/contexto histórico — corte de 12 turnos) |
| Orçamento mensal | **> US$ 5,00** acumulado no mês (NFR-15) | 🔴 `OrcamentoLLMEstourado` → congelar demo-heavy tests, revisar modelo (ADR-0005 permite troca por env) |
| Alavancas de custo (documentadas) | histórico 12 turnos · `max_tokens=500` · modelo por env · temperature 0.2 | — |

**Tracing de LLM (Langfuse/LangSmith) — decisão:** ficamos com **OTel + este
registro** (1 SDK, Etapa 18; custo/latência já capturados). Langfuse Cloud
free registrado como alternativa com gatilho: comparar versões de prompt com
UI/analytics de traces.

## 5. ✅ Portão de validação da Etapa 19

| Critério | Status |
|---|---|
| Eval bloqueia regressão no CI | ✅ E4+E3 (blockers) no PR; E1/E2 gates; job `evals-prompts` bloqueante p/ `prompts/**`; noturno completo |
| Custo por conversa monitorado com alerta de orçamento | ✅ registro por chamada + 2 alertas de FinOps (orçamento NFR-15) |
| Toda mudança de prompt passa pela suíte | ✅ path-trigger com LLM real — golden é a rede de segurança |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 20 liberada)*
