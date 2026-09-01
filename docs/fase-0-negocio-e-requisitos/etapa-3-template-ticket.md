# Template de Ticket

> Copie este template para cada task de `etapa-3-tasks.md` (ou issue no GitHub).
> Regra de ouro: **se um dev/agente precisa conversar com alguém para começar,
> o ticket está incompleto.**

```markdown
## T-XX — <verbo no infinito + objeto>

**Contexto:** por que esta task existe (1-3 frases, ligando à spec/NFR).

**Spec de referência:** `etapa-3-spec.md` §<seção> · US-<nn> · NFR-<nn>

**Entregáveis:**
- <arquivo/módulo/endpoint criado ou alterado>

**Restrições:**
- <o que NÃO fazer; convenções do AGENTS.md que se aplicam>

**Definition of Done (testável):**
- [ ] Teste <nome> escrito ANTES (TDD) e passando
- [ ] <comportamento observável verificável>
- [ ] <limites: cobertura, performance, etc.>

**Dependências:** T-XX (nenhuma | bloqueada por)

**Riscos/notas:** <opcional>
```

## Checklist antes de mover o ticket para "pronto"

- [ ] Teste nasceu antes da implementação (TDD — commit comprova)
- [ ] Vocabulário do glossário respeitado (sem sinônimos banidos)
- [ ] Nenhum `R$` fora de cotação da API · nenhuma PII crua em log
- [ ] DoD 100% marcada · CI verde
