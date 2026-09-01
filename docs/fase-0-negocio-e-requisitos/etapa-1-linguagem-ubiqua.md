# Etapa 1 — Linguagem Ubíqua (Glossário do Domínio)

> Fase 0 · Vocabulário compartilhado entre negócio e tecnologia. Regra: se um
> termo não está aqui, ele não entra em código, spec, commit message, log ou
> conversa. Cada termo tem **um nome só** — sinônimos são proibidos.

## Como usar

- **Em código:** nomes de classes, funções, tabelas e eventos saem DAQUI
  (traduzidos ao idioma técnico do contexto: `Quote`, `Handoff`, `Lead`).
- **Em discussão:** se alguém disser "a tela que mostra o preço", corrija para
  "a apresentação da **Cotação**".

---

## A — Atendimento

| Termo | Definição | Notas de fronteira |
|---|---|---|
| **Lead** | Pessoa que inicia contato buscando seguro de veículo | Vira "cliente" apenas após aceite + emissão (fora do nosso escopo) |
| **Conversa** | Sequência ordenada de mensagens entre lead e atendente (agente ou vendedor) | Identificada por `conversation_id`; ordena por `message_index`, **nunca** por timestamp (dataset tem timestamps fora de ordem) |
| **Mensagem** | Um turno na conversa: texto, imagem, áudio ou documento | Mídia chega como marcador (`[documento] CNH_frente.pdf`), sem conteúdo |
| **Canal** | Onde a conversa acontece | Produção: WhatsApp. Demo: web chat (Next). O agente é agnóstico ao canal |
| **Atendente** | Quem responde na conversa: o **Agente** (autônomo) ou o **Vendedor** (humano) | Nunca usar "bot" nos docs de negócio |
| **Agente** | O atendente autônomo que qualifica, cota e decide | Nosso produto core |
| **Qualificação** | Coleta dos dados mínimos para cotar: veículo (marca/modelo/ano), idade do lead, CEP onde o veículo dorme | Pode incluir e-mail/telefone/placa (opcionais) |
| **Desfecho** | Resultado final da conversa: `ganho`, `perdido`, `em_negociacao`, `sem_resposta` | Vocabulário herdado do dataset histórico |
| **Resolução autônoma** | Conversa concluída pelo Agente sem vendedor entrar | Base da métrica norte (TRA) |

## B — Cotação (Quoting)

| Termo | Definição | Notas de fronteira |
|---|---|---|
| **Cotação** | Preço calculado pelo sistema legado para um plano e um perfil | O Agente **nunca calcula nem estima** — só apresenta o que a API retornou |
| **Plano** | Produto de seguro: `essencial`, `completo`, `premium` | Com base mensal, franquia e coberturas próprias |
| **Prêmio** | Valor mensal final = base × multiplicadores | Em BRL |
| **Franquia** | Valor que o cliente paga em sinistro | Essencial 4.500 · Completo 3.000 · Premium 1.500 |
| **Multiplicadores** | Fatores que ajustam o prêmio: faixa etária, idade do veículo, região do CEP | Ex.: 18-24 anos = ×1.60; veículo 6-10 anos = ×1.15 |
| **Agravo de região** | ×1.30 para CEPs com prefixo `07 08 21 26 59` | Decisão da API, não do Agente |
| **Elegibilidade** | Regras que permitem ou recusam cotar: idade 18-75, veículo até 20 anos | Recusa = **422**, é regra de negócio, não erro |
| **Recusa de negócio** | Resposta 422 do legado (inelegível ou plano inexistente) | **Não se faz retry**; resposta honesta ou handoff |
| **Falha transiente** | Resposta 500/502/503 ou timeout do legado (20% + 10% lento de 8s) | **Se faz retry** com backoff; circuito abre se persistir |
| **Carência** | 30 dias até roubo/furto valerem, contados da vigência | Obrigatório informar ao apresentar Cotação |
| **Pró-rata de entrada** | Vigência começando no meio do mês → primeiro pagamento proporcional aos dias restantes | Calculado pelo legado; Agente informa |
| **Vigência** (`data_inicio`) | Data de início da cobertura | Opcional na qualificação |
| **ACL** | Camada anti-corrupção: retry, timeout, circuit breaker entre Agente e legado | Termo técnico do contexto Cotação |

## C — Escalonamento (Handoff)

| Termo | Definição | Notas de fronteira |
|---|---|---|
| **Handoff** | Transferência formal da Conversa do Agente para um Vendedor | Sempre gera registro com motivo |
| **Critério de handoff** | A regra explícita e auditável que dispara o Handoff | Ex.: recusa contestada, objeção complexa, pedido do lead, falha persistente do legado |
| **Motivo de handoff** | Categoria registrada: `inelegivel_contestado`, `objecao_preco`, `preferencia_humana`, `falha_tecnica`, `aceite_fechamento`, `fora_escopo` | Entra no contexto transferido ao Vendedor |
| **Fila de handoff** | Registro ordenado de conversas aguardando Vendedor | Na nossa stack: tabela no Postgres (ADR da Etapa 7) |

## D — Privacidade & Dados

| Termo | Definição | Notas de fronteira |
|---|---|---|
| **PII** | Dado pessoal identificável: CPF, e-mail, telefone, placa, CEP, nome | Presente solta no texto livre das mensagens |
| **Masking** | Substituição/mascaramento de PII por token antes de log/análise | Obrigatório em QUALQUER camada não-Bronze |
| **Bronze** | Dados brutos como recebidos (dataset original) | Acesso restrito; nunca vira demo |
| **Silver** | Dados limpos + PII mascarada + veículo normalizado | Base para evals e few-shot |
| **Injeção de prompt** | Tentativa do lead de manipular o Agente via mensagem | Tratada no threat model (Etapa 8) |

## E — Métricas

| Termo | Definição |
|---|---|
| **TRA** (Taxa de Resolução Autônoma) | % de leads elegíveis com cotação correta ponta a ponta sem humano — **métrica norte** |
| **TTFC** | Tempo até a primeira cotação válida |
| **Preço inventado** | Preço apresentado que não retornou da API — violação **zero-tolerance** |

---

## Sinônimos banidos (mapeamento rápido)

| ❌ Não usar | ✅ Usar |
|---|---|
| Bot / chatbot / assistente virtual | **Agente** |
| Orçamento / preço / valor | **Cotação** / **Prêmio** (o valor) |
| Cliente (antes do fechamento) | **Lead** |
| Transferir / passar pro time | **Handoff** |
| Erro da API (genérico) | **Falha transiente** (5xx) ou **Recusa de negócio** (422) |
| Atendimento humano | **Vendedor** (pessoa) / **Handoff** (ato) |
| Dados sensíveis / dados pessoais | **PII** |
