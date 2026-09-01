# Etapa 21 — Retrospectivas e Postmortems

> Fase 4 (fecha o processo) · **O loop que realimenta especificações e
> arquitetura.** Postmortem sem culpa em 48h · action items como tickets com
> dono e prazo · DORA a cada release.

---

## 1. Postmortem blameless — quando, como, prazo

**O que é "incidente relevante" (definição objetiva — sem subjetividade):**
- Qualquer acionamento de alerta **critical** (`DemoDown`, `PrecoSemOrigem`,
  `DBIndisponivel`, `OrcamentoLLMEstourado`), OU
- Queima de error budget de qualquer SLO (Etapa 18 §3), OU
- 1 única violação de preço sem origem (SLO-4 — zero-tolerance), OU
- Rollback automático executado (Etapa 16).

**Prazo: 48h** do fechamento do incidente. Template versionado em
[`docs/postmortems/TEMPLATE.md`](../postmortems/TEMPLATE.md) — arquivo
`YYYY-MM-DD-<slug>.md`. **Sem culpa**: pressuposto é processo/automação com
buraco, não pessoa — a Etapa 16 garante que nenhum código chega sem gates +
revisão, então incidente = lacuna do SISTEMA.

**Action item = ticket (regra dura):** cada ação do postmortem vira task do
template da Etapa 3 com **dono e prazo** — anotação solta é bug do postmortem.
Action item que realimenta spec/ADR cita a seção exata que muda (ex.: "spec §2
— revisar janela do half-open").

## 2. DORA a cada release (termômetro da entrega)

| Métrica | Como medimos (dados já existem) |
|---|---|
| **Deployment frequency** | runs do `release.yml` (GitHub) — alvo take-home: contínuo na fase ativa |
| **Lead time for changes** | timestamp do commit → smoke verde (o `release.yml` registra no summary) |
| **MTTR** | alerta disparado → rollback/resolução (Sentry + audit log; rollback automático já reduz para minutos) |
| **Change failure rate** | % de releases com rollback/smoke falho (o `LAST_GOOD_TAG` só é atualizado em sucesso — a variável é o contador) |

Registro: tabela por release na [`RETRO.md`](../../RETRO.md) (seção DORA) —
coleta manual de 4 números, 5 min por release; automação com dashboard fica
como gatilho de evolução (volume não justifica hoje).

## 3. O loop fecha — e JÁ funcionou neste projeto

O processo foi desenhado para aprender consigo mesmo. Dois loops reais já
ocorreram **durante** a escrita das etapas:

| # | Aprendizado | Realimentou | Quando |
|---|---|---|---|
| L1 | "Sem staging dedicado (custo)" era fraco contra o requisito do guia de staging-espelha-prod | **Etapa 17 reverteu a decisão da Etapa 8** (staging adotado, +US$3-5/mês) com nota deixada no próprio doc antigo | Etapa 17 |
| L2 | Conventional commits puro divergia do padrão do guia (gitmoji+inglês) | **Etapa 13 reescreveu a regra 6 do `AGENTS.md`** + commitlint custom | Etapa 13 |

*(L3 em andamento: a renumeração 18→21 do guia forçou tabela de mapeamento e
nota de numeração em 3 etapas — aprendizado: contratos de processo também
precisam de changelog. Registrado na RETRO.)*

A cada incidente real (pós-implementação), o postmortem segue o mesmo caminho:
aprendizado → PR em spec/ADR/alerta/runbook → suíte de testes pega a regressão.

## 4. RETRO.md do take-home

Materializada na raiz do repo ([`RETRO.md`](../../RETRO.md)) — esqueleto vivo:
o que já se pode registrar AGORA (o desenho do processo em si) + seções que
preenchem na implementação (T-01..T-17) e na entrega. Fecho obrigatório do
readme de entrega.

## 5. ✅ Portão de validação da Etapa 21 (e do processo)

| Critério | Status |
|---|---|
| Incidente relevante → postmortem em 48h | ✅ definição objetiva + template + prazo; incidentes reais só existem pós-implementação (ensaio T-15 gera o 1º exercício) |
| Action items com dono | ✅ regra dura: ticket do template Etapa 3, dono+prazo — sem anotação solta |
| DORA a cada release | ✅ 4 métricas mapeadas a dados existentes + registro por release na RETRO + step no `release.yml` |

---

*Validado em: 01/09/2026 pelo responsável do projeto — **PROCESSO COMPLETO (21/21)** · revisão final dos 22 portões em [`../checklist-final-implantacao.md`](../checklist-final-implantacao.md) · implementação T-01..T-17 liberada*
