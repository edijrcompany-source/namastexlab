# AI Log — Implementação do AutoSeguro Sales Agent (T-01 → T-16)

> **Transparência de uso de IA (entregável obrigatório do desafio).**
> Ferramenta: ZCode (agente de código, modelo GLM) orquestrado por comandos do
> autor. Formato: resumo estruturado por sessão — o processo completo
> (documento por documento, comando por comando) está no histórico git do repo
> e nas 21 etapas de `docs/`.
>
> Sanitização: sem chaves/tokens (verificado por scan de padrões + gitleaks no CI).

## Como a IA foi usada (o método — parte da avaliação)

- **Spec primeiro**: o autor forneceu guia de 21 etapas; a IA transformou em
  spec/ADRs/contratos com portões de validação, um por rodada, sempre com o
  autor validando antes de avançar.
- **TDD com divisão de papéis** (Etapa 14 §3): a IA escreve o teste que
  codifica a spec → RED verificado → implementa → GREEN + cobertura 100%.
  Commits `✅ test(...)` antes dos `✨ feat(...)` no histórico.
- **IA sob gates**: ruff (catraca) · import-linter (arquitetura C4) ·
  pytest-cov 100% · spectral · evals E1/E2/E3 — a IA nunca "desligou regra".

## Sessão 1 — Documentação (Fase 0 → Fase 4, 21 etapas)

- Input do autor: guia de processo (21 etapas) + desafio Namastex.
- A IA produziu: modelo de negócio/TRA, glossário, event storming, 16 US +
  18 NFRs, spec técnica (12 seções), 11 ADRs, contratos OpenAPI, threat model
  STRIDE, mensageria, IaC, observabilidade (SLOs/alertas), evals, governança.
- Decisões do autor em cada portão (ex.: gpt-4o-mini default, coverage
  90→99→100%, staging adotado, commits gitmoji).

## Sessão 2 — Implementação (T-01 → T-07, T-11)

- **T-01/T-02**: scaffold + masking (TDD: 21 testes RED→GREEN, 100%).
- **T-03 ACL**: breaker 5/30s/2 + backoff + NFR-04 simulado (97%+).
- **T-04 state machine**: tabela §1.3 + 4 invariantes; a invariável I3 pegou
  lacuna real (CORRIGE fora de QUALIFICANDO/CONFIRMANDO).
- **T-05 orchestrator**: C1-C6 verdes; eval E1 achou bug real (ano da
  data_inicio vazando p/ veículo); eval adversarial forçou price-guard a
  aceitar /planos (gap de design §6.8).
- **T-07 API**: endpoints §5.4 + wiring FakeLLM/OpenAI + C1 sobre HTTP contra
  o legado REAL (R$ 119,90 correto).
- **T-11 front**: chat Next mobile-first com QuoteCard/HandoffBanner.

## Sessão 3 — Dados, IA-avaliação e fechamento (T-08 → T-16)

- **T-08 Silver**: 26.470 msgs → PII 100% mascarada (0 vazamentos no scan).
- **T-09/T-10 evals**: E1 100% · E2 100% · E3 20/20 com gates no runner.
- **Refactor arquitetural**: import-linter pegou core→bordas; portas migradas
  para `domain/` (RETRO L4).
- **T-12/T-13**: fila /handoffs + export no chat.
- **T-16 TRA**: bateria 200 conversas no pior caso → **96,5%** (meta 70%).
- **Spectral**: contrato corrigido até 0 erros; codegen types commitados.

## Incidentes de processo (honestidade — também na RETRO)

- 2× um pipe `| tail` mascarou exit code do ruff e commit saiu com gate
  vermelho → detectado, corrigido no commit seguinte, fluxo mudou para
  `echo EXIT=$?` explícito (RETRO L5).
- 1 typo de replace (`com返 :=`) introduzido e revertido na hora.

## Prompts/nota

Sem prompts "mágicos": todo turno foi instrução de engenharia referenciando a
seção da spec/etapa. O contexto vivo (AGENTS.md) governou o comportamento da
IA — quiz de onboarding da Etapa 11 em ação.
