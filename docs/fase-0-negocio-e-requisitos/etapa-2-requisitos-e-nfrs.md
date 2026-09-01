# Etapa 2 — Requisitos Funcionais e NFRs

> Fase 0 · Derivado da Etapa 1 (modelo de negócio, linguagem ubíqua, event
> storming). Regra desta etapa: **NFR sem número é desejo** — todo NFR abaixo
> tem meta numérica e instrumento de medição; toda história tem critério de
> aceitação testável.
>
> Convenção: termos vêm do glossário (`etapa-1-linguagem-ubiqua.md`).
> Prioridade MoSCoW: **M**=Must · **S**=Should · **C**=Could.

---

## 1. User Stories

### Contexto: Atendimento

#### US-01 — Iniciar conversa `M`
> Como **Lead**, quero enviar a primeira mensagem e receber resposta imediata,
> para começar a resolver sem esperar um Vendedor.

Critérios de aceitação:
- **Dado** mensagem inicial do Lead (texto livre) **Quando** processada **Então** o Agente responde em ≤ 1 turno, saudando e pedindo exatamente os 3 dados da Qualificação (veículo, idade, CEP).
- **Dado** primeira mensagem **Então** `ConversaIniciada` é registrada com `conversation_id` gerado e status `ativa`.
- A resposta inicial **não** cita preços, planos ou valores.

#### US-02 — Qualificar via linguagem natural `M`
> Como **Lead**, quero passar meus dados como eu falo (texto solto), para não
> preencher formulário.

Critérios de aceitação:
- **Dado** "meu carro é um onix 2022, tenho 30 anos e o cep lá de casa é 01310-100" **Então** extração retorna `{veiculo_ano:2022, idade:30, cep:"01310-100"}` (marca/modelo capturados como texto livre para exibição).
- **Dado** dados parciais (ex.: só veículo) **Então** Agente pede **apenas** o que falta, sem repetir o que já tem.
- **Dado** mensagem de **mídia** (`image`/`audio`/`document`) **Então** Agente responde que não consegue abrir mídia e pede o dado em texto *(fecha H8)*.
- **Dado** dado inválido (idade 200, CEP "abc") **Então** Agente aponta o campo e pede novamente; nada é gravado como qualificado.
- Variante de formato: "e um Sandero 2022", "Toyota Corolla, ano 2008", "30 anos" — extração correta em ≥ 90% do conjunto de teste Silver *(ver NFR-10)*.

#### US-03 — Confirmar dados antes de cotar `S`
> Como **Lead**, quero confirmar o que o Agente entendeu, para evitar cotação errada.

Critérios de aceitação:
- **Dado** Qualificação completa **Então** Agente ecoa os 3 dados e pede confirmação ("é isso?").
- **Dado** Lead corrige um dado **Então** o campo é substituído (não duplicado) e novo eco é emitido.
- Extração confirmada gera evento `LeadQualificado` persistido.

### Contexto: Cotação

#### US-04 — Cotar e apresentar Cotação completa `M`
> Como **Lead** elegível, quero o preço real com todas as condições, para decidir.

Critérios de aceitação:
- **Dado** `LeadQualificado` + resposta 200 do legado **Então** Agente apresenta: **Prêmio mensal, franquia, coberturas do plano, carência de 30 dias para roubo/furto** e, se vigência informada não for dia 1º, o **pró-rata do primeiro pagamento**.
- Todo número apresentado corresponde **byte a byte** à resposta da API (`quote_id` gravado) *(guardrail da métrica norte)*.
- Se o Lead não escolher plano, Agente cota o `essencial` e **oferece comparativo** entre os 3 planos quando houver objeção *(ver US-09)*.
- Eventos `CotaçãoEmitida` e `CotaçãoApresentada` gravados com status e ids.

#### US-05 — Sobreviver à falha transiente do legado `M`
> Como **Lead**, quero minha cotação mesmo quando o sistema legado falha, sem
> esperar ou receber número inventado.

Critérios de aceitação:
- **Dado** resposta 500/502/503 ou timeout (> 3s) **Então** o cliente tenta novamente com backoff exponencial + jitter, até **3 tentativas totais**.
- **Dado** 3 tentativas falhas **Então** circuito abre; Agente responde ao Lead com mensagem honesta ("sistema de cotação indisponível, vou tentar novamente em X min") — **sem qualquer valor de preço**.
- **Dado** circuito aberto **Quando** expira janela de half-open **Então** nova tentativa é feita automaticamente e o Lead é notificado do resultado.
- **Dado** eventual sucesso **Então** fluxo segue normalmente (cotação atrasada é melhor que nenhuma).
- Parâmetros de resiliência são configuráveis por env e **assertados em teste** *(fecha H4)*.

#### US-06 — Tratar recusa de negócio (422) `M`
> Como Lead inelegível, quero uma recusa rápida e clara, para não perder tempo.

Critérios de aceitação:
- **Dado** 422 (`cotacao_recusada`) **Então** **zero retries**; Agente traduz o motivo em linguagem clara e empática.
- **Dado** Lead aceita a recusa **Então** `ConversaEncerrada {desfecho: perdido_ineligivel}`.
- **Dado** Lead contesta ("tem certeza? conheço gente que conseguiu") **Então** Handoff com motivo `inelegivel_contestado`.
- Nenhuma recusa demora mais de 1 turno após a resposta da API.

#### US-07 — Pré-elegibilidade de cortesia `S` *(fecha H1)*
> Como AutoSeguro, quero que o Agente detecte inelegibilidade óbvia antes de
> chamar o legado, para economizar chamadas.

Critérios de aceitação:
- **Dado** idade fora de 18-75 ou veículo com > 20 anos (calculado no ano corrente) **Então** Agente informa a inelegibilidade **sem** chamar a API — salvo se o Lead pedir confirmação formal, aí chama (a **verdade é sempre a resposta da API**).
- A regra local é uma cópia de cortesia declarada em código comum + teste de sincronia contra `plans.json` (falha se divergirem).

#### US-08 — Nunca inventar preço `M` *(política de domínio — fecha o guardrail)*
> Como AutoSeguro, quero garantia de que nenhum preço é fabricado, para
> proteger a marca e a conformidade.

Critérios de aceitação:
- Todo valor exibido ao Lead **deve** ter `quote_id` correspondente persistido — resposta sem `quote_id` é proibida por validação (camada de pós-processamento da fala do Agente, não só prompt).
- Números de moeda detectados na resposta do LLM sem origem na API → resposta é regenerada/bloqueada e o evento `TentativaDePrecoSemOrigem` é logado *(instrumento do NFR-09)*.

#### US-09 — Responder objeção de preço `S` *(fecha H3)*
> Como Lead, quero argumento real quando acho caro, para decidir.

Critérios de aceitação:
- **Dado** objeção de preço (1ª vez) **Então** Agente rebate **1 vez** com dados reais: comparativo de planos (prêmio × franquia × coberturas) vindos da API `GET /planos` — **sem desconto, sem "vou ver o que consigo"**.
- **Dado** 2ª objeção ou pedido de desconto **Então** Handoff com motivo `objecao_preco`.
- **Dado** Lead cita concorrente mais barata **Então** Agente não desqualifica a concorrente; oferta comparativo e mantém respeito.

### Contexto: Escalonamento

#### US-10 — Handoff com critério explícito e auditável `M` *(fecha H2 e H5)*
> Como Vendedor, quero receber conversas transferidas com motivo e contexto,
> para resolver rápido.

Critérios de aceitação:
- Handoff dispara **somente** pelos motivos: `aceite_fechamento` (Lead aceitou; emissão é humana), `inelegivel_contestado`, `objecao_preco`, `preferencia_humana` (**pedido explícito → imediato**, sem tentar convencer), `falha_tecnica` (circuito aberto + retentativa esgotada), `fora_escopo` (pedido fora de seguro auto).
- **Dado** handoff **Então** registro persiste: motivo, resumo da conversa, dados qualificados, cotações apresentadas (se houver), `conversation_id`.
- **Dado** handoff **Então** Agente informa ao Lead que um Vendedor humano vai continuar e **para de responder autonomamente**.
- A lista de motivos é código (enum), não texto livre.

#### US-11 — Fila de handoff visível `S`
> Como Vendedor, quero ver as conversas aguardando, para priorizar.

Critérios de aceitação:
- Front exibe fila ordenada por timestamp com motivo e tempo de espera; conversa legível na íntegra (com PII mascarada — NFR-12).

### Contexto: Privacidade & Dados

#### US-12 — Masking de PII em toda saída `M` *(fecha H7)*
> Como AutoSeguro (data controller), quero PII fora de logs e timeline, para
> cumprir a LGPD.

Critérios de aceitação:
- **Dado** qualquer log/timeline/dado de eval **Então** CPF, e-mail, telefone, placa aparecem mascarados (`389.***.***-43`, `u***@gmail.com`, `+55 11 *****-2584`, `GGE*3 0`→ formato definido na spec).
- **Dado** mensagem do Lead contendo PII **Quando** enviada ao LLM **Então** PII é mascarada **antes** do envio; des-mascaramento só na camada Bronze persistida (acesso restrito) *(decisão LGPD — ver seção 4)*.

#### US-13 — Pipeline Bronze→Silver do dataset `S`
> Como engenharia, quero o dataset mascarado e normalizado, para usar em
> evals e few-shot sem expor PII.

Critérios de aceitação:
- Bronze = parquet original intocado; Silver = mensagens com PII mascarada, `veiculo_texto` normalizado (marca/modelo/ano), conversas ordenadas por `message_index`.
- Silver é a **única** base consumida por evals/few-shot; processo reprodutível por comando único.

### Contexto: Front/Demo & Observabilidade

#### US-14 — Chat de demo com timeline rastreável `M`
> Como Avaliador, quero conversar com o Agente e ver o rastro de cada decisão,
> para avaliar a entrega.

Critérios de aceitação:
- Chat web (Next) responde em mobile-first (≥360px).
- Timeline mostra por mensagem: `conversation_id`, papel, status; para Cotações: `quote_id`, tentativas, tempo, status do circuito.
- Estados visíveis: conversando → qualificando → cotando (com spinner e tentativa corrente) → cotação/handoff.

#### US-15 — Log de execução exportável `M`
> Como Avaliador, quero o log de uma conversa completa (início→cotação), exigido
> pela entrega.

Critérios de aceitação:
- Botão exporta a conversa completa (JSON + Markdown legível) incluindo ids, status, retries e tempos — é o artefato `log-execucao` do README da entrega.

#### US-16 — Healthcheck e rastreabilidade `M`
> Como operação, quero saber se o sistema está vivo e reconstituir qualquer
> conversa depois.

Critérios de aceitação:
- `GET /health` do agent-api retorna status próprio **e** do legado (via ping barato, cacheado).
- Cada evento da conversa é persistido com `conversation_id`, timestamp, tipo e payload — reconstituição completa por consulta.

---

## 2. Matriz de NFRs

> Cada linha: atributo · meta **numérica** · instrumento de medição · quando
> se mede. Metas calibradas pelo comportamento real do legado (20% falha,
> 10% lenta/8s).

| ID | Atributo | Meta numérica | Instrumento de medição | Quando |
|---|---|---|---|---|
| NFR-01 | Latência por turno (agent-api, caminho feliz, sem legado lento) | **p95 < 5 s** | Histograma de duração por turno nos logs estruturados + teste k6 local (50 turnos) | Dev contínuo + CI |
| NFR-02 | Timeout do cliente `/quote` | **3 s** (< 8s do legado) | Constante assertada em teste unitário + teste com relógio fake | CI (TDD) |
| NFR-03 | TTFC — tempo até primeira Cotação apresentada (caminho feliz) | **< 2 min** | Δt entre `ConversaIniciada` e `CotaçãoApresentada` no log; verificado em eval E2E | CI + demo |
| NFR-04 | Cotação obtida mesmo com legado instável | **≥ 95%** de sucesso eventual | Simulação determinística: 1.000 cotações contra mock com p_falha=0.30 por tentativa (3 tentativas ⇒ falha total 2.7%) | CI (TDD) |
| NFR-05 | Circuit breaker | Abre com **5 falhas consecutivas**; half-open após **30 s**; fecha com **2 sucessos** | Teste unitário com relógio fake | CI (TDD) |
| NFR-06 | Disponibilidade da demo | **≥ 99%** mensal | UptimeRobot/Better Stack pingando `/health` a cada 5 min | Produção |
| NFR-07 | RPO / RTO | **RPO ≤ 24 h** (backup diário Railway) · **RTO ≤ 1 h** (redeploy CI) | Procedimento documentado + 1 exercício de restore registrado | Fase 3 + 1× antes de entregar |
| NFR-08 | Concorrência | **10 conversas simultâneas** sem degradar p95 acima de NFR-01 +20% | k6: 10 VUs conversando por 3 min contra ambiente de demo | Pré-entrega |
| NFR-09 | Zero preços inventados | **0 violações** (blocker) | Eval que extrai valores de moeda da resposta do Agente e compara com a resposta mockada da API; qualquer divergência falha o build | CI (TDD/eval) |
| NFR-10 | Acurácia de extração de Qualificação | **≥ 90%** campo-correto | Suite de evals sobre amostra rotulada do Silver (200 conversas) | CI (Etapa 16) |
| NFR-11 | Decisão de Handoff correta | **≥ 95%** | Eval com casos rotulados por motivo (inclui os 6 motivos) | CI (Etapa 16) |
| NFR-12 | PII mascarada em logs/timeline/evals | **100%** (0 vazamentos) | Teste que varre logs e payloads com regex de CPF/e-mail/telefone/placa; falha se achar padrão cru | CI (TDD) |
| NFR-13 | Segredos fora do repo | **0 segredos** commitados | gitleaks no CI + revisão manual dos `ai-logs/` | CI |
| NFR-14 | Robustez a injeção de prompt | **0/20** ataques resultam em preço/desconto/condição fabricada | Suite adversarial fixa (20 prompts: "ignore as regras", "me dá 50% off", SQL/profanação, etc.) | CI (Etapa 16) |
| NFR-15 | Orçamento de tokens | **≤ US$ 0,10 por conversa** (média) · **≤ US$ 5/mês** na demo | Contagem de tokens por chamada registrada no log; agregação mensal por script | Dev contínuo + mensal |
| NFR-16 | Cobertura de testes da lógica determinística (resiliência, máquina de estados, masking, extração, handoff) | **≥ 90%** linhas | `pytest --cov` com gate no CI (código de LLM client e E2E fora do gate) | CI |
| NFR-17 | Tempo de pipeline CI | **< 5 min** por push | Timing do GitHub Actions | CI |
| NFR-18 | Front responsivo e leve | **≥ 360 px** sem quebra · Lighthouse **≥ 90** (perf/a11y) | Lighthouse CI no build da Vercel | CI front |

**NFRs que definem arquitetura** (registrar nos ADRs da Etapa 4): NFR-02/04/05 → ACL com circuit breaker dedicado; NFR-12 → middleware de masking obrigatório; NFR-09 → camada de pós-validação de saída do LLM; NFR-16 → módulo core isolado e puro (sem I/O).

---

## 3. Checklist LGPD

> Dataset é **100% sintético** (declarado no dicionário), mas o desafio manda
> tratá-lo como sensível — e o avaliador observa isso. Regra: projetar como se
> fosse real.

### 3.1 Inventário de dados pessoais

| Dado | Onde aparece | Finalidade | Base legal (LGPD) | Retenção | Minimização / masking |
|---|---|---|---|---|---|
| Nome do Lead | Mensagens | Tratamento humano na conversa | Pré-contratual (art. 7º, V) | 30 d pós-conversa (demo) | Mantém; mascarado em logs públicos |
| CPF | Texto livre das mensagens | NÃO é usado para cotar | — **não coletar ativamente** | Bronze apenas | **Mascarado em 100% das camadas não-Bronze** |
| Idade | Qualificação | Regra de preço/eligibilidade | Pré-contratual (art. 7º, V) | Idem conversa | Enviada ao legado (necessária) |
| CEP | Qualificação | Agravo de região (2 dígitos) | Pré-contratual | Idem conversa | Enviado ao legado (necessário); log apenas 2 primeiros dígitos |
| E-mail, telefone, placa | Opcionais, se o Lead oferecer | Contato futuro do Vendedor | Pré-contratual | Idem conversa | Mascarados em logs/timeline |
| Conteúdo de mídia | Marcadores apenas | — | — | **Não armazenamos mídia** | Fora de escopo por design |
| Histórico de conversa | Postgres | Rastreabilidade e evals | Legítimo interesse (art. 7º, IX) | 30 d (demo) / dados sintéticos sem limite | PII mascarada em qualquer export |

### 3.2 Decisões LGPD registradas

1. **Coleta ativa mínima:** Agente pede **somente** veículo, idade e CEP (o necessário para cotar). CPF só se o Lead oferecer e for encaminhar para fechamento — e nunca é necessário para a Cotação.
2. **Masking antes do LLM (US-12):** mensagens são mascaradas **antes** de irem ao provedor de LLM; CPF/e-mail/telefone/placa viajam como tokens (`[CPF_1]`). Idade e CEP são mascarados só em logs — precisam ir íntegros ao legado (finalidade específica).
3. **Transferência internacional:** provedor de LLM processa fora do BR → risco registrado; mitigação = item 2 (minimização) + adotar provedor com retenção zero quando houver opção. Em produção real: DPO decide região. *(dataset sintético torna o risco aceitável na demo)*
4. **Direitos do titular:** endpoint admin `DELETE /conversations/{id}` (direito à eliminação) e relatório de quais dados existem por conversa.
5. **Retenção:** job de purga apaga conversas com > 30 dias na demo; Bronze sintético pode persistir.

---

## 4. Definition of Ready (história entra em desenvolvimento só se…)

- [ ] Critérios de aceitação escritos em Given/When/Then (testáveis sem interpretação)
- [ ] NFRs impactados listados por ID
- [ ] Vocabulário 100% do glossário (sem sinônimos banidos)
- [ ] Comportamento definido para: preço (só da API), handoff (motivo do enum), falha do legado
- [ ] Dependências de contrato resolvidas (payload `/quote`, schema interno)
- [ ] Nome do teste que vai nascer primeiro (TDD) escrito na história
- [ ] Estimativa MoSCoW atribuída

---

## 5. Matriz de rastreabilidade

| História | NFRs atrelados | Onde se valida | Hotspot fechado |
|---|---|---|---|
| US-01/02/03 | 01, 10, 12 | CI unit + evals | H8 |
| US-04 | 03, 09, 12 | CI unit + eval E2E | — |
| US-05 | 02, 04, 05, 06 | CI unit (relógio fake) + simulação | H4 |
| US-06 | 04 | CI unit | — |
| US-07 | — | CI unit (sync c/ plans.json) | H1 |
| US-08 | 09 | CI unit (pós-validação de saída) | — (guardrail) |
| US-09 | 09 | evals | H3 |
| US-10/11 | 11, 12 | CI unit + evals | H2, H5 |
| US-12 | 12, 13 | CI (regex scan) | H7 |
| US-13 | 12, 10 | script + CI | — |
| US-14/15 | 01, 18 | Lighthouse CI + manual | — |
| US-16 | 06 | CI smoke | — |
| (todos) | 14 (injeção) | evals adversariais | H6 |

---

## 6. ✅ Portão de validação da Etapa 2

| Critério do portão | Status |
|---|---|
| Cada NFR tem **número** e **instrumento de medição** | ✅ 18/18 na matriz (seções 2) |
| Toda história tem **critério de aceitação testável** | ✅ 16/16 em Given/When/Then ou checagem objetiva |
| Hotspots H1-H8 do event storming endereçados | ✅ mapeados em US/NFR (seção 5) |
| LGPD com inventário, base legal, retenção e minimização | ✅ seção 3 |

**Decisões de comportamento fechadas nesta etapa** (detalhamento técnico fica
para a spec da Etapa 3): H1 pré-elegibilidade de cortesia · H2 aceite→handoff
de fechamento · H3 uma rebatida com dados reais · H4 parâmetros de resiliência
(3 tentativas, timeout 3s, breaker 5/30s/2) · H5 humano imediato · H6 suite
adversarial 20 casos · H7 masking obrigatório · H8 mídia→pedir texto.

---

*Validado em: 01/09/2026 pelo responsável do projeto (portão atendido — Etapa 3 liberada)*
