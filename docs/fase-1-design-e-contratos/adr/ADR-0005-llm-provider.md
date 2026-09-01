# ADR-0005 — LLM: abstração de provider + default OpenAI gpt-4o-mini

**Status:** aceito (01/09/2026)

## Contexto
O turno exige: output **JSON estrito** (spec §4.1), latência ~2-4s (NFR-01
p95 5s), custo ≤ US$ 0,10/conversa (NFR-15), PT-BR natural. Sem dependência
de features exóticas (sem tool-calling, sem function-calling — o JSON do
turno é fixo).

## Decisão
1. **Porta `LLMPort`** (interface): `completar(prompt, contexto) -> TurnoJSON`.
   Implementações: `OpenAIClient` (default) e `FakeLLM` (testes/CI — 100%
   determinístico, sem rede).
2. **Default de produção: OpenAI `gpt-4o-mini`**, JSON mode, `temperature=0.2`,
   `max_tokens=500`. Troca por env (`LLM_PROVIDER`, `LLM_MODEL`) **sem refactor**.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Anthropic Claude Haiku** | Qualidade PT-BR alta, tool-use forte | JSON estrito exige prompt-engineering extra (sem JSON mode nativo na linha Haiku usada); custo similar | Reserva — troca por env |
| **Gemini Flash** | Preço baixo, rápido | JSON mode menos previsível na época da avaliação; segunda opção | Reserva |
| **LLM local (Ollama)** | Custo zero, dados não saem | Qualidade/latência insuficientes para NFR-01 no hardware da demo; setup a mais | Descartado |
| **gpt-4o (grande)** | Margem de qualidade | Custo 10-15× acima do orçamento NFR-15 sem ganho para este domínio | Descartado |

## Consequências
**Positivas:** CI roda sem rede/chave (FakeLLM) — NFR-09/14 são testáveis
offline; troca de provider é config, não código; JSON mode nativo casado com
o schema §4.1.
**Negativas/riscos:** dependência da OpenAI em produção (rate limit/latência) →
mitigado: retry no client + fallback canônico de resposta (spec §6) já cobre
falha total do LLM em um turno (mensagem de espera honesta).
**LGPD:** mensagens vão mascaradas (US-12) — risco de transferência
internacional minimizado; registrado no checklist LGPD.
