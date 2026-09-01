# Etapa 6 — Tratamento de Erros e Resiliência

> Fase 1 · **Erro é parte do contrato, não acidente.** Consolida e completa o
> que a spec (§2/§6) e o contrato do legado já definiram. Fontes cruzadas:
> `etapa-3-spec.md` §1-§6 · `openapi/agent-api.yaml` · `openapi/quote-api.yaml`.

---

## 1. Princípios

1. **Dois planos distintos de falha** — confundir os dois é o erro mais comum:
   - **Erro de protocolo** (o pedido não pode ser atendido): RFC 7807
     `problem+json`, código estável, correlation ID. Ex.: conversa inexistente.
   - **Desfecho de negócio** (o pedido foi atendido e o RESULTADO é uma má
     notícia): resposta **200** do turno com `reply` + `eventos`.
     Ex.: recusa de elegibilidade, falha persistente do legado, handoff.
     **Recusa de cotação NÃO é erro HTTP** — é conteúdo da conversa.
2. **Nunca vazar stack trace** — `detail` do problem+json é mensagem humana;
   detalhe técnico vai só para o log (com o mesmo correlation ID).
3. **Falha do Agente nunca inventa dados** — em qualquer fallback, a resposta
   canônica omite valores (preço, prazo) que não venham de resposta real.

## 2. Formato único de falha — RFC 7807 + extensões

```json
{
  "type": "https://autoseguro.dev/problems/conversa-nao-encontrada",
  "title": "Conversa não encontrada",
  "status": 404,
  "detail": "Não achamos essa conversa. Ela pode ter sido apagada (LGPD) ou o link está incorreto.",
  "instance": "/conversations/01J8Z.../messages",
  "correlation_id": "f3a1c9e2-7b4d-4e8a-9c21-5d6b8e0a1f2c"
}
```

**Código estável = slug do `type`** (`conversa-nao-encontrada`). O `title` pode
ser reescrito; o slug **nunca muda** (compatibilidade = semver do contrato,
Etapa 5 §4).

**Correlation ID:** o client envia `X-Correlation-Id` (UUID v4 por turno; o
front gera com `crypto.randomUUID()`); ausente → o server gera. Ele:
- ecoa no problem+json (`correlation_id`);
- é logado em TODOS os eventos do turno e no log estruturado (Etapa 18);
- aparece na UI de erro ("código de suporte").

## 3. Catálogo de erros (códigos estáveis)

### 3.1 Inbound — erros do agent-api

| Código (`type` slug) | HTTP | Quando | `detail` humano | Retryável? |
|---|---|---|---|---|
| `conversa-nao-encontrada` | 404 | ULID inexistente ou apagada (LGPD) | "Não achamos essa conversa…" | Não |
| `payload-invalido` | 422 | Schema falha: `text`+`media_marker` juntos, ambos vazios, `text` > 4000 | descreve o campo | Corrigir e reenviar |
| `limite-taxa-excedido` | 429 | > 10 req/min por IP (demo) — `Retry-After: 60` | "Muitas mensagens seguidas…" | Sim (após Retry-After) |
| `nao-autorizado` | 401 | `adminToken` ausente/incorreto (DELETE, admin) | "Operação administrativa." | Não |
| `servico-indisponivel` | 503 | Postgres fora / app degradado (health `degradado`) | "Sistema temporariamente fora…" | Sim |
| `erro-interno` | 500 | Exceção não mapeada | "Algo saiu do ar do nosso lado. Use o código de suporte." | Sim |

### 3.2 Outbound — erros do legado (`quote-api`) e tradução

| Legado responde | Classificação | Ação do agent-api (spec §1.3) | Plano |
|---|---|---|---|
| 500/502/503 `upstream_unavailable` | **Transiente** | retry (§4.1) → circuito → reply honesta §6.6 → retentativa 2 min → 2ª abertura: handoff `falha_tecnica` | Negócio (200) |
| Timeout (> 3s — inclui a resposta lenta de 8s) | **Transiente** | idem acima | Negócio (200) |
| 422 `cotacao_recusada{motivo}` | **Recusa de negócio** | sem retry; reply empática §6.5; contestação → handoff `inelegivel_contestado` | Negócio (200) |
| 400 `payload_invalido` | **Bug nosso** (payload validado antes não deveria falhar) | log ERROR + correlation ID; reply honesta; NÃO retry; 2ª ocorrência → handoff `falha_tecnica`; alerta de bug | Negócio (200) + bug interno |

### 3.3 Erros de dependência interna (viram desfecho, não problem+json)

| Situação | Desfecho na conversa | Evento |
|---|---|---|
| LLM fora (timeout/5xx após retry+breaker) | Reply canônica por estado (catálogo §5.3 da spec — sem LLM) | `llm_unavailable` *(novo no enum)* |
| Price-guard violado 2× | Fallback canônico da apresentação | `price_guard_violation` |
| DB fora no meio do turno | Falha o turno inteiro (transação) → `servico-indisponivel` (503) + correlation ID | log ERROR |

## 4. Política de resiliência por dependência

### 4.1 Matriz única (consolida spec §2 + adiciona LLM/DB)

| Dependência | Timeout | Retry | Backoff + jitter | Circuit breaker | Fallback | Idempotência |
|---|---|---|---|---|---|---|
| **quote-api** (legado) | **3 s**/tentativa | **3** tentativas totais | 500 ms · 1000 ms + jitter U(0, 250) | abre: **5** falhas consecutivas · half-open: **30 s** · fecha: **2** sucessos | Reply honesta §6.6 + retentativa **2 min** + handoff na 2ª abertura na mesma conversa | Cálculo puro, sem efeito colateral → **retry naturalmente idempotente** |
| **LLM provider** | **15 s**/turno | **1** retry | 500 ms + jitter U(0, 100) | abre: **5** consecutivas · half-open: **60 s** · fecha: **2** sucessos | Reply **canônica por estado** (template fixo, sem LLM); breaker aberto = falha rápida sem pagar timeout | Leitura pura → idempotente |
| **Postgres** | connect **3 s** · statement **5 s** | Pool reconecta (3× automático) | — | **N/A** (serviço próprio gerenciado; breaker aqui só mascararia) | Fail-fast: turno falha inteiro → 503 `servico-indisponivel` + correlation ID | Transação atômica por turno (eventos+resposta juntos) — **sem retry cego** |
| *(front → agent-api)* | client fetch **15 s** | 1 retry idempotente | — | — | UI de erro + correlation ID (§6) | via `Idempotency-Key` (§5) |

### 4.2 Idempotência de retentativa (nova regra)

1. **`POST /conversations/{id}/messages` aceita header `Idempotency-Key`**
   (≤64 chars, opcional). Duplicado na janela de **2 min** → responde o turno
   **original** (replay) com header `Idempotency-Replayed: true`. Sem ele,
   retry de rede pode duplicar mensagem — documentado como risco do client.
2. **Cotação é idempotente por natureza** (cálculo puro): os retries da §4.1
   nunca geram cobrança/efeito colateral; só o **sucesso** grava
   `quote_succeeded` (falhas gravam `quote_attempt_failed{attempt, reason}`).
3. Front usa a mesma `Idempotency-Key` para reenvio automático pós-timeout.

### 4.3 Consolidação com a spec

A spec §2 permanece a fonte dos parâmetros do legado; esta etapa **adiciona**
LLM e Postgres à política e a regra de idempotência. Mudanças aplicadas na
spec/contrato por esta etapa (aditivas, regenerar types):

- `TipoEvento` += `llm_unavailable`
- `Problem` += `correlation_id` (extensão RFC 7807)
- `POST /messages` += header opcional `Idempotency-Key` (+ resposta
  `Idempotency-Replayed`)

## 5. Degradación graceful (o que o Agente faz com o mundo caindo)

| Cenário | UX do Lead | UX do Vendedor/Operação |
|---|---|---|
| Legado fora (circuito aberto) | "Sistema de cotação indisponível; vou tentar de novo em instantes" — **sem R$** | Evento `circuit_state_changed` no log; health `legado: degradado` |
| LLM fora | Respostas canônicas por estado (funcional, menos charme) | Evento `llm_unavailable`; health continua `ok` |
| Ambos | Handoff `falha_tecnica` com contexto | Fila de handoff |
| DB fora | 503 + correlation ID (front mostra código de suporte) | Alerta (Etapa 18: health externo) |

## 6. Front — erros com rosto humano

| Item | Especificação |
|---|---|
| **Error boundaries** | `app/error.tsx` (rota) + boundary global `app/global-error.tsx` (Next App Router); fallback renderiza mensagem + correlation ID, nunca tela branca |
| **Estado de erro por tela** | `/` (chat): banner **não-bloqueante** acima do input + botão reenviar (usa Idempotency-Key) · `/handoffs`: distingue `vazio` (fila limpa ≠ erro) de `erro` (banner + retry) · export: toast com retry |
| **Mensagem humana padrão** | "Opa, algo saiu do ar do nosso lado 🙈 Já registramos com o código **{correlation_id curto}**. Tenta de novo em instantes — ou atualiza a página." |
| **Correlation ID na UI** | Exibido no banner de erro e no rodapé do chat (discreto, copiável); gerado pelo front, aceito pelo server |
| **Timeout de client** | Fetch 15 s → trata como erro de rede → banner + retry idempotente |

## 7. ✅ Portão de validação da Etapa 6

| Critério | Status |
|---|---|
| Todo erro com código estável + HTTP mapeados | ✅ §3 (6 inbound + 4 de legado + 3 internos) |
| Cada dependência externa com timeout/retry/breaker definidos | ✅ §4.1 (legado, LLM, Postgres — N/A justificado, front) |
| Front exibe mensagem humana + correlation ID | ✅ §6 (+ contrato: `Problem.correlation_id`) |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 7 liberada)*
