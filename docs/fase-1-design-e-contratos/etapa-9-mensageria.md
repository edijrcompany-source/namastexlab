# Etapa 9 — Mensageria e Eventos

> Fase 1 · "Decidir o que é evento é decisão de negócio, não técnica."
> Transporte decidido no [ADR-0010](./adr/ADR-0010-sem-broker-postgres-como-transporte.md):
> **sem broker — Postgres** (outbox + `SKIP LOCKED` + DLQ), com envelope
> público versionado que sobrevive a qualquer migração futura de transporte.

---

## 1. O que é evento (decisão de negócio)

Dos 18 tipos internos (spec §5.2), **6 são eventos de negócio** — fatos que
outro sistema precisaria saber. O resto é **rastreabilidade interna**
(observabilidade da conversa, Etapa 18).

| Evento público (`type`) | Gatilho de negócio | Payload mínimo (PII-safe) |
|---|---|---|
| `conversation.started` | Lead enviou a 1ª mensagem | `conversation_id`, `canal` |
| `lead.qualified` | Dados confirmados pelo Lead | `veiculo_ano`, `idade`, **`cep_prefixo`** (2 dígitos — o mesmo que o agravo usa), `plano_id` |
| `quote.succeeded` | Cotação obtida no legado | `quote_id`, `plano_id`, `premio_mensal`, `franquia`, `multiplicadores`, `tentativas`, `duracao_ms` |
| `quote.refused` | Recusa de negócio (422) | `motivo_slug` (`idade_acima_limite` \| `veiculo_acima_20_anos` \| `plano_inexistente`) |
| `handoff.requested` | Conversa transferida a humano | `motivo` (enum da spec §5.3) |
| `conversation.ended` | Conversa encerrada | `desfecho`, `duracao_s`, `tra` (bool: resoluta sem humano) |

**Regra de PII:** evento público **nunca** carrega PII — nem CPF (nunca
coletamos), nem CEP íntegro (só prefixo), nem texto de mensagem. Dado
minimizado por design (LGPD, Etapa 2 §3).

## 2. Consistência — transactional outbox (já é o design)

Eventos são gravados **na mesma transação do turno** (Etapa 6 §4.1: "transação
atômica por turno") — a tabela `events` **é** a outbox. Logo: **não existe**
a classe de bug "ação executada sem evento" ou "evento sem ação". Consumidor
futuro lê a outbox por cursor (`seq` global já ordena) — sem polling de
tabela inteira.

## 3. Contrato dos eventos — envelope versionado

Um JSON Schema por evento, versionado por **campo `event_version`** (não por
URL), compatibilidade **aditiva** (mesma política semver da Etapa 5 §4:
novo campo opcional = minor; remover/required novo = major ⇒ `v2` paralelo).

Envelope canônico (ex.: `quote.succeeded`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://autoseguro.dev/schemas/quote.succeeded.v1.json",
  "type": "object",
  "required": ["event_id", "event_version", "type", "occurred_at", "conversation_id", "correlation_id", "data"],
  "properties": {
    "event_id":          { "type": "string", "pattern": "^[0-9A-HJKMNP-TV-Z]{26}$" },
    "event_version":     { "const": 1 },
    "type":              { "const": "quote.succeeded" },
    "occurred_at":       { "type": "string", "format": "date-time" },
    "conversation_id":   { "type": "string", "pattern": "^[0-9A-HJKMNP-TV-Z]{26}$" },
    "correlation_id":    { "type": "string", "format": "uuid" },
    "data": {
      "type": "object",
      "required": ["quote_id", "plano_id", "premio_mensal", "franquia", "moeda", "tentativas", "duracao_ms"],
      "properties": {
        "quote_id":       { "type": "string" },
        "plano_id":       { "enum": ["essencial", "completo", "premium"] },
        "premio_mensal":  { "type": "number", "multipleOf": 0.01 },
        "franquia":       { "type": "number" },
        "multiplicadores":{ "type": "object" },
        "tentativas":     { "type": "integer", "minimum": 1, "maximum": 3 },
        "duracao_ms":     { "type": "integer" }
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": false
}
```

Os 6 schemas vivem em `docs/…/schemas/eventos/*.v1.json` quando o repo nascer
(Etapa 11) e são validados em CI (fixture de cada evento público contra o
schema). *(AsyncAPI fica registrado como ferramenta aplicável quando existir
transporte com filas reais — hoje o "AsyncAPI do projeto" é esta seção + os
JSON Schemas.)*

## 4. Fila de tarefas interna — `retry_quote` (a promessa da spec §1.3)

**Worker assíncrono leve no próprio agent-api** (asyncio, tick a cada 15s)
que executa a retentativa de cotação. Semântica de mensageria completa:

### 4.1 Claim com lease (worker morre no meio → outro assume)

```sql
UPDATE conversations
SET retry_lease_expires_at = now() + interval '60 seconds',
    retry_attempts = retry_attempts + 1
WHERE id IN (
  SELECT id FROM conversations
  WHERE retry_pending AND encerrada_em IS NULL
    AND (retry_lease_expires_at IS NULL OR retry_lease_expires_at < now())
  ORDER BY atualizada_em
  LIMIT 10
  FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

`SKIP LOCKED` permite múltiplos workers sem disputa; lease de 60s cobre o
pior caso de processamento (3 tentativas × 3s timeout + backoff).

### 4.2 Processamento (idempotente por construção)

1. **Recheck de estado:** se `retry_pending = false` (outro worker concluiu)
   → aborta silenciosamente *(idempotência de efeito)*.
2. Tenta a cotação pela ACL (spec §2 — cálculo puro, idempotente).
3. **Sucesso:** grava eventos + resposta na timeline → `retry_pending = false`
   (transação única). O Lead vê no próximo turno/sync.
4. **Falha com circuito reaberto na mesma conversa**
   (`circuito_reaberturas ≥ 2`): handoff `falha_tecnica` (spec §1.3) → fim.
5. **Falha com circuito fechado/half-open:** reagenda com **backoff
   exponencial**: 2 → 4 → 8 min, **máx 5 tentativas** → handoff
   `falha_tecnica`.

### 4.3 DLQ — mensagem venenosa

Exceção **inesperada** (bug, dado corrompido) no worker:

- capturada por tentativa; após **3 erros inesperados** → linha em
  `dead_letters` (`task_type`, `conversation_id`, `motivo` stack curta,
  `tentativas`, `criada_em`) → `retry_pending = false` + handoff
  `falha_tecnica` (Lead nunca fica no limbo) + alerta (Etapa 18);
- **o worker continua o loop** — venenosa não derruba o fluxo.

### 4.4 Migração `0002` (delta da Etapa 8)

```
dead_letters        (id BIGSERIAL, task_type, conversation_id, motivo TEXT,
                     tentativas INT, criada_em)              [nova tabela]
conversations       + retry_attempts INT DEFAULT 0
                    + retry_lease_expires_at TIMESTAMPTZ NULL [colunas aditivas]
```

## 5. Consumidor idempotente — regras gerais

| Consumidor | Idempotência |
|---|---|
| Worker `retry_quote` | recheck de estado + cotação pura + transação única |
| Vendedor (fila handoffs) | `handoffs.status` com transição atômica `pendente→em_atendimento` (`UPDATE ... WHERE status='pendente'` — segundo clique é no-op) |
| Consumidor futuro da outbox | dedup por `event_id` (PK) — reprocessar é seguro por design at-least-once |

## 6. ✅ Portão de validação da Etapa 9 (os 2 testes, como TDD)

| Teste do portão | Implementação |
|---|---|
| **Matar o consumidor no meio e religar sem duplicar efeitos** | `test_worker_kill_and_resume`: worker A faz claim (lease) → "morre" (correloutine cancelada antes de concluir) → relógio fake avança 60s → worker B re-claima → assert: **exatamente 1** `quote_succeeded`, 1 resposta na timeline, `retry_attempts` refletindo os claims |
| **Mensagem venenosa termina na DLQ sem derrubar o fluxo** | `test_poison_message_dlq`: fixture cujo processamento lança sempre → 3 ciclos → linha em `dead_letters` com motivo → worker processa a PRÓXIMA tarefa da fila com sucesso → nada crasha |

Ambos com relógio fake + Postgres de teste (compose) — sem emulação de fila
externa (LocalStack N/A: sem AWS no stack — nota no ADR-0010).

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 10 liberada)*
