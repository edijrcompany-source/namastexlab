# Etapa 1 — Modelo de Negócio e Domínio

> Fase 0 · Documento fundador. Tudo o que vem depois (requisitos, spec, ADRs)
> herda o vocabulário e o recorte definidos aqui.
>
> **Fontes:** análise completa do repositório `namastex-fde-challenge`
> (README, `plans.json`, `quote_logic.py`, gerador do dataset, dicionário).

---

## 1. O problema

A **AutoSeguro** (seguradora fictícia de veículos) vende por WhatsApp: leads
chegam, um time de **4 vendedores humanos** (`Camila, Rodrigo, Patricia,
Marcos` no dataset) qualifica, consulta preço num **sistema legado de cotação
e apresenta a oferta.

### Dores mapeadas (evidências do desafio)

| # | Dor | Evidência objetiva |
|---|---|---|
| 1 | **Atendimento humano não escala** | 4 vendedores para todo o funil; 20% das conversas do dataset terminam em `sem_resposta` — lead esperou e ninguém voltou |
| 2 | **Sistema legado instável trava o vendedor** | A `/quote` falha em **20%** das chamadas (500/502/503) e demora **8s** em **10%** — o vendedor fica bloqueado ou improvisa |
| 3 | **Leads inelegíveis consomem funil inteiro** | Idades do dataset vão até 82 (API recusa 76+) e veículos até 2001 (em 2026, >20 anos = recusa) → **~30% dos leads são matematicamente incotáveis**, mas hoje são atendidos por humano até o fim |
| 4 | **Sem cobertura 24/7** | Lead de madrugada/fim de semana espera horas pela primeira resposta |
| 5 | **Risco de preço errado** | Com sistema lento, a tentação é "chutar" preço — e no dataset os vendedores informam preços que **não batem** com as regras reais da API (ex.: "Premium R$ 129,90" vs. base R$ 339,90) |

### Consequência de negócio
Funil caro e lento: cada cotação custa minutos de um vendedor humano, ~1/3
desse tempo é gasto com leads que nunca poderiam ser cotados, e 1/5 dos leads
nem recebe resposta.

---

## 2. Público e personas

### Segmentos de cliente

| Segmento | Descrição | Papel |
|---|---|---|
| **Leads elegíveis** | 18-75 anos, veículo com até 20 anos, qualquer região do Brasil | Usuário final do agente |
| **Leads inelegíveis** | 76+ anos ou veículo 21+ anos (~30% do funil atual) | Precisam de recusa rápida e honesta |
| **Time de vendas (interno)** | Os 4 vendedores que hoje fazem tudo | Recebem handoffs qualificados |
| **AutoSeguro (a empresa)** | Operação e resultado do funil | Paga a conta e define a régua |

### Personas (derivadas da análise do dataset — revisão humana aplicada)

| Persona | Perfil | O que testa no produto |
|---|---|---|
| **Carlos, 32** — o impaciente | Onix 2022, CEP de alto risco (prefixo 07/08/21/26/59), chama 22h de terça | Caminho feliz + agravo de região + 24/7 |
| **Marlene, 68** — a cética | Corolla 2015, "prefiro falar com gente" | Elegível (mult. 1.40) + **critério de handoff por preferência humana** |
| **Zeca, 79** — o inelegível | Gol 2004, insiste no atendimento | Recusa dupla (76+ e veículo 22 anos) → **recusa rápida, sem queimar vendedor** |
| **Rafaela, 27** — a negociadora | HB20 2019, "vi mais barato na Porto" (mult. 1.25) | Objeção de preço + não inventar desconto |

> A IA (análise do gerador do dataset) sugeriu a base demográfica; a seleção
> de personas e o recorte de "o que testa" foram feitos sobre as regras reais
> de `plans.json` — fluxo discovery-com-IA-com-revisão-humana, como pede o guia.

---

## 3. Proposta de valor

> **Para o lead:** cotação correta em minutos, a qualquer hora, sem esperar
> vendedor — e um humano de verdade quando o caso pede.
>
> **Para a AutoSeguro:** funil que escala sem escalar headcount; vendedores
> só entram onde agregam; **zero preço inventado** (o preço vem SEMPRE da API).

**Diferencial defensável:** o agente não é um chatbot que "conversa bonito" —
é um agente operacional que (a) trata a instabilidade do legado como parte do
trabalho (retry, timeout, circuit breaker), (b) nunca fabrica número e
(c) escala para humano com critério explícito e auditável.

---

## 4. Business Model Canvas

| | | |
|---|---|---|
| **Parcerias-chave**<br>• Sistema legado de cotação (quote-api)<br>• Provedor LLM<br>• Canal WhatsApp<br>• (futuro) seguradoras subjacentes | **Atividades-chave**<br>• Qualificação conversacional<br>• Cotação com resiliência<br>• Handoff com contexto<br>• Evals e monitoramento contínuo | **Proposta de valor**<br>• Cotação 24/7 em minutos<br>• Preço sempre correto (via API)<br>• Humano quando importa<br>• Recusa rápida para inelegíveis |
| **Recursos-chave**<br>• Agente IA (agent-api)<br>• Dataset de 2.500 conversas (treino/evals)<br>• Time de vendas p/ handoff<br>• Infra Railway/Vercel | **Relacionamento**<br>• Conversacional automatizado com escalonamento<br>• Transparência em falhas ("sistema fora, volto em X min") | **Canais**<br>• WhatsApp (canal do negócio)<br>• Web chat (demo desta entrega) |
| **Estrutura de custos**<br>• Tokens de LLM<br>• Infra (~US$ 5-10/mês)<br>• Vendedores humanos (agora focados no handoff) | | **Fluxos de receita**<br>• Prêmios mensais: Essencial R$ 119,90 · Completo R$ 209,90 · Premium R$ 339,90 (base, antes de multiplicadores) |
| | **Segmentos** = seção 2 | |

---

## 5. Métrica norte

### 🎯 Taxa de Resolução Autônoma (TRA)

> **% de leads elegíveis que recebem uma cotação correta de ponta a ponta
> (conversa → qualificação → cotação válida → decisão registrada) sem
> qualquer intervenção humana.**

**Por que esta e não outra:**

| Candidata | Por que não é a norte |
|---|---|
| Conversão em venda | Depende de emissão/apólice/pagamento — **fora do escopo** do agente (não existe API de fechamento) |
| Custo por atendimento | Consequência da TRA, não causa; e difícil medir em demo |
| NPS | Requer volume e tempo que um take-home não tem |
| **TRA** ✅ | É **exatamente o escopo do agente**, é mensurável nos nossos logs, e é o que o desafio avalia ("o que ele faz quando a /quote falha?") |

**Guardrails que acompanham a norte** (uma métrica sem guardrails vira alvo
de trapaça):
- 🚫 **Zero preços inventados** — preço apresentado ⇔ preço retornado pela API (violations = 0, inaceitável)
- ⏱️ Tempo até primeira cotação válida < 2 min no caminho feliz
- 📉 Taxa de handoff por falha técnica (vs. por regra de negócio) — falha técnica alta = resiliência ruim

**Meta inicial:** TRA ≥ 70% dos leads elegíveis (baseline do dataset: ~0%,
pois hoje tudo passa por humano; 30% dos em_negociacao + 28% ganho indicam o
teto realista de autonomia do funil).

### Métricas de segundo nível
1. Tempo-médio até primeira cotação (TTFC)
2. Acurácia de extração de dados (evals — Etapa 16)
3. % de handoffs com critério correto (evals)
4. Taxa de leads inelegíveis recusados sem tocar vendedor (meta: 100%)

---

## 6. Domínio — DDD leve

### Bounded contexts

| Contexto | Tipo | Responsabilidade | Dono |
|---|---|---|---|
| **Atendimento** (Conversation) | 🧠 Core | Dialogar, qualificar, manter estado da conversa, decidir encaminhamento | agent-api |
| **Cotação** (Quoting) | 🔧 Supporting | Ser cliente do legado: ACL com retry/backoff/circuit-breaker, distinguir 5xx (transiente) de 422 (recusa de negócio), apresentar carência/pró-rata corretamente | agent-api (módulo) |
| **Escalonamento** (Handoff) | 🔧 Supporting | Fila de transferência para vendedor humano com contexto completo e motivo registrado | agent-api + Postgres |
| **Privacidade & Dados** (Privacy) | 🛡️ Genérico/cross-cutting | Masking de PII (CPF, e-mail, telefone, placa, CEP), camadas Bronze→Silver, retenção LGPD | todos os serviços |

### Context map (relações)

```
                      ┌──────────────────────┐
                      │     ATENDIMENTO      │
                      │  (core: conversa,    │
                      │   qualificação,      │
                      │   decisão)           │
                      └──┬────────┬────────┬─┘
             Customer/  │        │ evento │
             Supplier   │        │ "Handoff-
             via ACL    │        │  Solicitado"
        ┌───────────────▼──┐  ┌─▼──────────────┐
        │     COTAÇÃO      │  │ ESCALONAMENTO  │
        │ ┌──────────────┐ │  │ (fila humana)  │
        │ │ ACL: retry + │ │  └────────────────┘
        │ │ circuit      │ │
        │ └──────┬───────┘ │        todos ↓ consomem
        └────────┼─────────┘  ┌──────────────────┐
                 ▼            │   PRIVACIDADE    │
        [sistema legado       │ masking · LGPD · │
         quote-api — NÃO      │ Bronze→Silver    │
         alteramos]           └──────────────────┘
```

**Insight arquitetural do domínio:** o quote-api É o "sistema legado
que nem sempre colabora" — nossa camada de resiliência é, em DDD, uma
**Anti-Corruption Layer** literal: traduz e protege o core (Atendimento) da
instabilidade do supplier.

### Fronteiras de escopo (o que NÃO é nosso)

- ❌ Emissão de apólice/boleto (não existe API; handoff ao aceitar)
- ❌ Subscrição/precificação (regras são do legado, só consumimos)
- ❌ Integração real com WhatsApp (demo via web chat no front Next)

---

## 7. ✅ Portão de validação da Etapa 1

> **Para os leads de seguro auto da AutoSeguro no WhatsApp — 30% dos quais são
> inelegíveis e todos hoje dependem de 4 vendedores atolados num sistema que
> falha 30% das vezes — a dor é esperar atendimento humano lento para descobrir
> se conseguem, e por quanto, segurar o carro; entregamos um agente que
> qualifica, cota e decide sozinho 24/7 com preço sempre calculado pela API e
> escalonamento humano de critério explícito — e o sucesso é medido pela
> Taxa de Resolução Autônoma: % de leads elegíveis com cotação correta de
> ponta a ponta sem intervenção humana (meta ≥ 70%).**

**Para quem:** leads elegíveis (e a própria AutoSeguro, que destrava o funil).
**Qual dor:** espera por humano + instabilidade do legado + inelegíveis queimando funil.
**Como se mede:** TRA ≥ 70%, com guardrails de zero-preço-inventado.

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 2 liberada)*
