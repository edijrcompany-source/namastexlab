<!-- Auditabilidade (Etapa 20 §1): o PR responde "quem pediu o quê, o que a IA gerou, quem aprovou" -->

## Contexto

- Ticket/task: <!-- T-XX e link -->
- Spec de referência: <!-- ex.: etapa-3-spec.md §2 — SEM spec citada, PR não entra -->

## O que mudou

<!-- resumo curto; comportamento observável -->

## Checklist do autor (humano ou agente de IA)

- [ ] Teste escrito ANTES (TDD — o PR mostra o teste vermelho→verde)
- [ ] `make lint && make test` verdes localmente
- [ ] Nenhum valor monetário fora de resposta da API (regra 1)
- [ ] Nenhuma PII crua em log/export/teste (regra 2)
- [ ] `quote-service/` e `dataset/` intocados (regra 3)
- [ ] Docs atualizadas se comportamento mudou (gerada não se escreve à mão — Etapa 12)
- [ ] Se toca `prompts/**`: suíte evals rodou com LLM real + `prompts/CHANGELOG.md` atualizado (Etapa 19/20)
- [ ] Se a IA gerou este código: **export da sessão commitado em `ai-logs/`** (sanitizado — Etapa 20 §2)

## Para o revisor humano (obrigatório — IA nunca aprova sozinha)

- [ ] O código corresponde à spec citada (não ao "gosto")
- [ ] Commits no padrão gitmoji (atomicidade verificada)
