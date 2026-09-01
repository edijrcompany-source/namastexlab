# Etapa 7 — Internacionalização (i18n)

> Fase 1 · Escopo: **pt-BR único** (decisão de design desde a Fase 0) com
> infraestrutura i18n completa — catálogo único, chaves semânticas, formatos
> centralizados, locale negociado, lint e pseudo-locale. Detalhes no
> [ADR-0009](./adr/ADR-0009-locale-unico-ptbr-catalogo-compartilhado.md).

---

## 1. Decisões de idioma e formato

| Dimensão | Decisão | Onde vive |
|---|---|---|
| Idioma | `pt-BR` único (negociação: `cookie locale` > `Accept-Language` > `pt-BR`) | ADR-0009 |
| Moeda (exibição) | `R$ 1.234,56` (pt-BR, vírgula decimal, ponto milhar) | util formato |
| Moeda (transporte) | número JSON (`209.9`) — **nunca** string formatada | contrato |
| Data/hora (transporte) | ISO 8601 **UTC** (`2026-09-01T12:00:00Z`) | contrato |
| Data/hora (exibição) | `dd/mm/aaaa HH:mm` em `America/Sao_Paulo` | util formato |
| Datas de negócio | `data_inicio` sem TZ = meia-noite local do Lead (pró-rata usa o mês dela); timeout de inatividade e purga LGPD calculados em **UTC** | spec §1.3 + §7 |

## 2. Catálogo único (`messages/pt-BR.json`)

- **Um JSON compartilhado** por API e front — materializa as canônicas da
  spec §6, os erros da Etapa 6 e a UI. Chaves semânticas por namespace:

| Namespace | Conteúdo | Quem usa |
|---|---|---|
| `agent.*` | 24 mensagens canônicas/fallback do Agente (saudação, recusas, falha honesta, handoffs por motivo, apresentação fallback com placeholders) | turn orchestrator + price-guard fallback |
| `api.erro.*` | 6 problemas do catálogo (chave = **código estável** da Etapa 6) | problem+json |
| `ui.*` | ~30 strings de tela (chat, handoffs, erros, common) | front |

- **Interpolação `{placeholder}`** — zero concatenação de fragmentos. Composição
  permitida apenas de **frases inteiras** (ex.: fallback de apresentação =
  `cotacao_apresentacao_fallback` + linha opcional `cotacao_prorata_linha`).
- **Keyword de teste = texto do catálogo**: os asserts de "elementos
  obrigatórios" (spec §6) verificam a fala do LLM contra strings vindas do
  catálogo — uma fonte só.
- `t()` mínimo (~30 linhas) por lado; tipagem TS **gerada do JSON**
  (guardião de chaves — mesmo princípio do codegen da Etapa 5).

## 3. Formatos centralizados — um util por camada

| Camada | Util | Funções | Implementação |
|---|---|---|---|
| Front | `apps/web/src/lib/format.ts` | `formatBRL`, `formatDate`, `formatDateTime`, `formatCep` | `Intl.NumberFormat`/`DateTimeFormat` com locale da constante `LOCALE = 'pt-BR'`, tz `America/Sao_Paulo` |
| Back | `services/agent-api/…/core/formatting.py` | `format_brl` (para canônicas com moeda), `utc_now` | stdlib, sem I/O — puro, TDD |

Regra: **nenhum outro ponto do código formata moeda/data** — violação pega no
review e no teste AST (§5).

## 4. Erros da API por locale

problem+json (Etapa 6): `type` slug = código estável (imutável); `title` e
`detail` **resolvidos do catálogo** pelo locale negociado. Hoje resolve sempre
pt-BR; com um segundo locale, o mecanismo já está no lugar (só trocar a
resolução). O **contrato não muda** — strings continuam no schema `Problem`.

## 5. Enforcement — "zero string crua" com lint pegando

| Camada | Mecanismo | Exceções documentadas |
|---|---|---|
| Front | **eslint `react/jsx-no-literals`** + `no-restricted-syntax` p/ template strings em JSX | símbolos, números, aria-técnicos |
| Back | teste `test_no_raw_strings.py`: **AST** dos módulos `api/` e `conversation/` — literais PT com espaço+letra fora do catálogo falham, com **allowlist versionada** | logs técnicos (inglês, engenharia), enums de eventos, nomes de plano (dados, não UI) |
| Ambos | teste de **completude**: chaves referenciadas existem no catálogo (e nenhuma órfã) | — |

## 6. Pseudo-locale (`pt-X-TEST`) — teste que passa no CI

Script `scripts/pseudo_locale.py` gera do catálogo: cada string vira
`⟦texto expandido ~35%⟧` (multibyte de propósito). Os testes:

1. **Placeholders intactos**: `{veiculo}` etc. sobrevivem à transformação
   (contagem antes == depois) em 100% das chaves.
2. **Limites**: `title` ≤ 120 chars, `detail` ≤ 300 chars no pseudo (detecta
   chave que cresceu demais para a UI).
3. **UTF-8 ponta a ponta**: pseudo com `⟦⟧` atravessa API (problem+json) e
   render do front sem `?` de encoding.
4. **Layout smoke** (Playwright, Etapa 14): chat e fila renderizam com pseudo
   sem overflow horizontal em 360px.

## 7. ✅ Portão de validação da Etapa 7

| Critério | Status |
|---|---|
| Zero string crua no código (lint pega) | ✅ plano: eslint jsx-no-literals + teste AST com allowlist (§5) |
| Erros da API: código + mensagem por locale | ✅ `type` slug + `title/detail` do catálogo resolvido por locale (§4) |
| Formatos centralizados em um único util | ✅ 1 util por camada, tabela única de padrões (§1/§3) |
| Teste pseudo-locale passa | ✅ 4 testes especificados (§6), entram no CI com a Fase 2/3 |

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 8 liberada)*
