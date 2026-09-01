# RETRO — AutoSeguro Sales Agent (Namastex FDE Challenge)

> Retrospectiva viva do take-home (Etapa 21). Seções marcadas ⏳ preenchem
> durante a implementação (T-01..T-17); o resto já é registro real.

## Como este projeto foi construído (resumo honesto)

Processo completo de **4 fases / 21 etapas** executado ANTES do código
(`docs/README.md` tem a trilha com portões de validação): negócio e domínio →
spec → arquitetura (11 ADRs) → contratos OpenAPI → dados/mensageria →
segurança → repo/context engineering → docs vivas → padronização → testes →
containers → CI/CD → ambientes/IaC → observabilidade → evals → governança →
retro. **TDD de ponta a ponta: o teste que codifica a spec é do autor; a
implementação que o satisfaz é da IA** (Etapa 14 §3).

## O que funcionou de cara ✅

- **Spec antes do código**: a Etapa 3 (`etapa-3-spec.md`) acabou respondendo
  perguntas que surgiriam no meio da implementação (mídia? 2ª objeção? CEP
  `00000-000`?) — todas tinham resposta pronta.
- **Event storming primeiro**: os 8 hotspots viraram requisitos (H6 injeção →
  suite adversarial; H7 PII → masking como módulo puro TDD).
- **A instabilidade do legado como cidadão de primeira classe**: a ACL da
  Etapa 6 (matriz por dependência) é o coração do desafio e nasceu desenhada,
  não remendada.
- **Determinismo no E2E** (`QUOTE_SEED=42`): transformou o sistema instável
  (o tema do desafio!) em testes estáveis.
- **Uso de IA como processo auditável**: ai-logs + PR template + gates — a
  régua do desafio ("as conversas com IA fazem parte da entrega") virou
  arquitetura, não promessa.

## Loops de aprendizado reais (o processo se corrigindo)

| # | O que aconteceu | O que mudou |
|---|---|---|
| L1 | Decisão "sem staging" (Etapa 8) era fraca vs. requisito do guia | Etapa 17 adotou staging + deixou nota no doc antigo |
| L2 | Convenção de commits divergia do padrão do guia | Etapa 13 reescreveu regra do AGENTS.md + commitlint custom |
| L3 | Rennumeração do guia (18→21 etapas) quebrou referências cruzadas | Tabela de mapeamento no docs/README.md — aprendizado: processo também precisa de changelog |
| L4 | **import-linter pegou o núcleo importando bordas** (orchestrator → llm/quoting) — o contrato C4 §3 vale desde a 1ª linha | Refactor T-09: portas/exceções/extração/price-guard migrados para `domain/` (onde contratos moram); bordas só implementam |
| L5 | **Pipe `\| tail` mascarou exit code do ruff** 2× e commit saiu com gate vermelho | Gates agora verificados com `echo EXIT=$?` explícito (nunca pipe antes de `&&`); lição registrada no AGENTS? Não — no fluxo: sempre exit code |

## O que faria diferente 🔄 (⏳ atualizar na entrega)

- ⏳ Pontos de friction na implementação T-01..T-17 (registrar aqui)
- ⏳ Onde a spec errou por excesso/ausência e exigiu PR de correção
- ⏳ Tempos reais: planejamento (21 etapas) vs. implementação vs. entregáveis

## Incidentes e postmortems ⏳

Nenhum incidente real até aqui (sistema ainda não implantado). Ensaio de
incidente (Etapa 18 §5, 4 simulações em staging) gera o primeiro exercício no
T-15. Templates e regra 48h: `docs/postmortems/`.

## DORA por release ⏳ (Etapa 21 §2)

| Release (sha) | Data | Lead time (commit→smoke) | Deploy freq (dia) | MTTR | Change failure rate |
|---|---|---|---|---|---|
| | | | | | |

*(coleta: 4 números, 5 min por release — dados do GitHub Actions + Sentry)*

## Números finais (preencher na entrega) ⏳

- [ ] TRA na bateria simulada (meta ≥70%) · TTFC p95 (meta <2min)
- [ ] Evals: E1 __% · E2 __% · E3 0/20 · E4 0 violações
- [ ] Custo LLM por conversa (meta ≤US$0,10) · mensal (≤US$5)
- [ ] Coverage lógica determinística (meta ≥90%) · mutmut núcleo (≥60%)
- [ ] Uptime da demo durante a avaliação (meta ≥99%)

## Próximos passos (se o projeto continuasse)

- ⏳ Implementação via tasks T-01..T-17 (`etapa-3-tasks.md`) em ordem de
  dependência — Épico A (fundações) primeiro.
