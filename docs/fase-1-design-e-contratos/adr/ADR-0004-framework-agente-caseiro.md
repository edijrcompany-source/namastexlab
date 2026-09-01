# ADR-0004 — Framework de agente caseiro fino (sem LangGraph/LangChain)

**Status:** aceito (01/09/2026)

## Contexto
O "agente" deste sistema é: máquina de estados finita (spec §1, 7 estados,
tabela fechada) + 1 chamada de LLM por turno com output JSON estruturado +
guardrail de preço por código (spec §4.3). Toda a lógica de decisão é
determinística e especificada — o LLM faz NLU+NLG, não decide.

## Decisão
**Implementação caseira fina**: state machine própria (pura, TDD) + cliente
LLM próprio (com retry simples) + orchestrator de turno. **Sem** LangChain,
LangGraph, OpenAI Agents SDK, CrewAI ou similares.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **LangGraph** | Grafos de estado prontos, checkpointing | Nosso grafo é pequeno e JÁ está especificado como tabela testável; abstração de grafo adiciona indireção entre spec e código; TDD do fluxo fica acoplado ao framework | Descartada |
| **OpenAI Agents SDK** | Tool-calling nativo, handoffs prontos | Lock-in de provider; "handoff" do SDK ≠ nosso handoff de negócio (fila humana auditável); controle fino do guardrail mais difícil | Descartada |
| **Pydantic AI** | Type-safety de output (JSON) | Soluciona só a camada que é trivial de isolar; mais uma dependência | Descartada |
| **Caseiro fino** ✅ | Spec=implementação 1:1 · domínio puro 100% testável sem LLM/framework (NFR-16) · guardrail de preço injetado no ponto exato · zero lock-in · rastreabilidade total dos eventos | Manter retry do LLM client nós mesmos; sem tracing grátis | **Aceita** |

## Consequências
**Positivas:** o diferencial avaliado (resiliência + rastreabilidade) fica em
código nosso, legível pelo avaliador; state machine em tabela única é
auditável contra a spec §1 linha a linha.
**Negativas/riscos:** menos baterias (observabilidade de prompts, tracing) →
mitigado: logging estruturado próprio (Etapa 15) + prompts versionados em
arquivo (Etapa 17). Se o domínio crescesse (multi-agente, ferramentas
dinâmicas), reavaliar LangGraph — gatilho registrado.
