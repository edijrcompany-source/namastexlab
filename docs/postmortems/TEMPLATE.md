# Postmortem — <título curto do incidente>

> **Blameless (Etapa 21 §1):** o pressuposto é lacuna de processo/automação —
> nunca pessoa. Preencher em até **48h** do fechamento. Nome do arquivo:
> `YYYY-MM-DD-<slug>.md`.

| Campo | Valor |
|---|---|
| **Data/hora início (UTC)** | |
| **Detectado por** | alerta `<nome>` / smoke / manual |
| **Severidade** | critical / warning |
| **SLOs atingidos** | ex.: SLO-1 (queimou X% do budget) |
| **Duração (MTTR)** | alerta → resolução |
| **Escopo** | conversas afetadas / demo fora / etc. |

## Cronologia (UTC)

| Hora | Evento | Evidência (link: trace/log/PR) |
|---|---|---|
| | alerta disparou | |
| | ação tomada | |
| | resolução (rollback? fix?) | |

## Causa raiz

<!-- técnica — pergunte "por quê?" até chegar a processo/automação -->

## Impacto

- Conversas/turnos afetados:
- Error budget consumido:
- Custos (tokens/infra):

## O que funcionou / o que falhou

- ✅ (ex.: rollback automático agiu em 2min)
- ❌ (ex.: alerta chegou 10min depois do sintoma)

## Action items (TODOS viram ticket com dono e prazo)

| # | Ação | Realimenta | Ticket | Dono | Prazo |
|---|---|---|---|---|---|
| 1 | | spec §X / ADR-00XX / alerta / runbook | T-XX | | |

## Lições → loop

Especificar exatamente o que muda em spec/ADR/alerta/runbook/eval para a classe
de defeito nunca mais passar despercebida.
