# ADR-0009 — Locale único pt-BR com catálogo centralizado compartilhado

**Status:** aceito (01/09/2026)

## Contexto
Público 100% BR (dataset, desafio e demo); multi-idioma é fora de escopo desde
a Fase 0. Mas o guia é claro: string de tela cravada no código é débito que
cresce com juros — hoje as mensagens vivem espalhadas (spec §6, catálogo de
erros da Etapa 6, UI futura), e o problema aparece na primeira mudança de
texto ou no primeiro segundo idioma.

## Decisão
1. **Locale único: `pt-BR`** — negociação existe mas resolve sempre para ele:
   `cookie locale` > `Accept-Language` > `pt-BR`.
2. **Catálogo único compartilhado** API ↔ front: **um JSON**
   (`messages/pt-BR.json`) importado pelos dois lados (Python: `json.load`;
   TS: `resolveJsonModule`). Fonte de design hoje em `docs/`; vira arquivo
   real do repo na Etapa 11.
3. **Chaves semânticas com namespace** — `agent.*` (canônicas do Agente),
   `api.erro.*` (chave = código estável da Etapa 6), `ui.*` (front).
   Interpolação por `{placeholder}`. **Zero concatenação** de fragmentos.
4. **Formatos centralizados**: transporte sempre ISO 8601 **UTC** e números
   JSON (`209.9`); exibição pt-BR (moeda `R$ 1.234,56`, data `dd/mm/aaaa`,
   fuso `America/Sao_Paulo`) — **um util por camada** (`formatting.py` /
   `format.ts`), derivados da mesma tabela de padrões (Etapa 7 §3).
5. **Enforcement**: front — `react/jsx-no-literals` (eslint pega); back —
   teste AST com allowlist; **pseudo-locale** (`pt-X-TEST`) gerado do catálogo
   valida comprimento, placeholders e UTF-8 no CI.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **next-intl / i18next** | Routing de locale, plurais ICU | ~50 strings, 1 locale — peso morto; mais dependência | Reserva p/ multi-idioma real |
| **ICU MessageFormat** | Plural/gênero/ selective | pt-BR único não usa nenhum deles; complexidade nos dois runtimes | Reserva (junto com next-intl) |
| **Catálogos separados** (py + ts) | Cada lado independente | Divergem silenciosamente — o débito que o guia alerta | Descartada |
| **Strings in-line + refactor "quando precisar"** | Zero setup | Débito com juros; quebra o portão | Descartada |
| **JSON único + util mínimo `t()`** ✅ | Uma verdade; tipagem TS gerada do JSON (guardião); troca de idioma = 1 arquivo | `t()` próprio a manter (~30 linhas) | **Aceita** |

## Consequências
**Positivas:** trocar/enxugar texto é PR de 1 arquivo com diff reviewável; o
problem+json ganha `title/detail` do catálogo sem tocar contrato (código
estável já é a chave); teste de completude impede chave órfã/faltante em CI.
**Negativas/riscos:** `t()` caseiro (se locale 2 chegar, migrar para
next-intl + ICU — gatilho registrado); JSON compartilhado exige disciplina de
import (mitigada pela tipagem gerada e pelo teste de completude).
**Nota LLM:** respostas livres do Agente são geradas em pt-BR por instrução de
prompt (versão do prompt na Etapa 20) — o i18n cobre as **canônicas/fallback**,
erros e UI; a checagem de "elementos obrigatórios" (spec §6) usa as mesmas
strings do catálogo como keywords.
