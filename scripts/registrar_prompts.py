# Registra os 40 prompts da sessão em ai-logs/prompts — 1 arquivo + 1 commit por prompt.
import datetime
import io
import os
import subprocess

P = [
(1,"analise-seguranca-desafio","decisao","Analise todos os arquivos desta pasta do desafio técnico: identifique vulnerabilidades, scripts maliciosos e o contexto geral. Apenas visão geral, sem desenvolvimento."),
(2,"adocao-guia-processo","etapa","Adotaremos um processo guiado antes de desenvolver: 4 fases com etapas numeradas (modelo de negócio até retro/postmortems), cada uma com portão de validação. Aqui está o sumário."),
(3,"stack-front-back","decisao","Teremos também uma camada de front em Next.js, com deploy na Vercel; backend na Railway; metodologia TDD. Confirme a arquitetura conteinerizada e as ferramentas de CI/CD, mensageria e observabilidade. Sem desenvolvimento por ora."),
(4,"etapa-1-negocio","etapa","Execute a Etapa 1 (modelo de negócio e domínio): salve a documentação na estrutura adequada, aplique DDD leve (bounded contexts e linguagem ubíqua), Business Model Canvas, event storming e uma métrica norte. Atenda ao portão de validação."),
(5,"etapa-2-requisitos","etapa","Execute a Etapa 2 (requisitos funcionais e NFRs): user stories com critérios testáveis, matriz de NFRs com meta numérica e instrumento de medição, checklist LGPD e Definition of Ready."),
(6,"etapa-3-spec","etapa","Execute a Etapa 3 (spec-driven development): a especificação como artefato principal — máquina de estados, parâmetros finais, formatos exatos, casos de aceite, tasks T-01..T-17 e template de ticket. Implementável sem perguntas."),
(7,"regra-readme-sempre","feedback","Regra permanente: atualize o docs/README.md ao final de toda etapa (status, índice e validação)."),
(8,"etapa-4-arquitetura","etapa","Execute a Etapa 4 (arquitetura e ADRs): modelagem C4 nos três níveis e ADRs com contexto, decisão, alternativas e consequências para toda decisão estrutural."),
(9,"validacao-adrs","validacao","OK — validar a Etapa 4, incluindo o default gpt-4o-mini no ADR-0005."),
(10,"etapa-5-contratos","etapa","Execute a Etapa 5 (contratos API-first): OpenAPI antes do código; front gera types; mock server; contract tests bloqueiam CI. Atualize também o cronograma para o guia de 21 etapas."),
(11,"etapa-6-erros","etapa","Execute a Etapa 6 (erros e resiliência): RFC 7807 com correlation ID; catálogo de códigos estáveis; política por dependência (timeout, retry+backoff, circuit breaker, fallback, idempotência); front com error boundaries e mensagem humana."),
(12,"etapa-7-i18n","etapa","Execute a Etapa 7 (internacionalização): zero string crua, catálogo único API-front, formatos centralizados, locale negociado e teste pseudo-locale."),
(13,"etapa-8-dados","etapa","Execute a Etapa 8 (modelo de dados e migrações): schema e ERD versionados, Alembic com expand-migrate-contract, rollback testado e backup com restore comprovado."),
(14,"etapa-9-mensageria","etapa","Execute a Etapa 9 (mensageria e eventos): outbox pattern, idempotência no consumidor, DLQ para mensagens venenosas, retry com backoff e schema versionado."),
(15,"etapa-10-threat-model","etapa","Execute a Etapa 10 (threat modeling): STRIDE em uma página, superfícies de ataque, segredos por ambiente, SAST no CI e scan de segredos."),
(16,"etapa-11-repo","etapa","Execute a Etapa 11 (estrutura do repo e context engineering): monorepo de propósito, AGENTS.md como artefato, docs-as-code e Dev Container."),
(17,"etapa-12-docs-vivas","etapa","Execute a Etapa 12 (documentação viva): o que pode ser gerado é proibido escrever à mão; portal publicado no pipeline; Diátaxis para a prosa."),
(18,"etapa-13-padronizacao","etapa","Execute a Etapa 13 (padronização automatizada): ruff/eslint/prettier, pre-commit, commitlint com gitmoji em inglês, micro-commits atômicos e política de catraca (zero aviso novo)."),
(19,"etapa-14-testes","etapa","Execute a Etapa 14 (testes unificados): pirâmide única para o produto — unit, integração, contrato, componente e E2E com Playwright; mutation testing no núcleo."),
(20,"etapa-15-containers","etapa","Execute a Etapa 15 (containers): imagem multi-stage, base slim, processo não-root, um comando sobe tudo, hadolint e scan de CVE."),
(21,"etapa-16-cicd","etapa","Execute a Etapa 16 (CI/CD): trunk-based com feature flags, gates em ordem (lint, testes, build, scan, deploy, smoke, rollback automático), preview por PR e revisão humana obrigatória."),
(22,"etapa-17-ambientes","etapa","Execute a Etapa 17 (ambientes e IaC): dev/staging/prod idêndicos por construção, infra declarativa com plan revisado em PR e detecção de drift."),
(23,"etapa-18-observabilidade","etapa","Execute a Etapa 18 (observabilidade): OpenTelemetry como SDK único, correlation ID ponta a ponta, SLOs com error budget e alertas sempre com runbook."),
(24,"etapa-19-evals","etapa","Execute a Etapa 19 (avaliação contínua de IA): casos dourados versionados, rastreio de custo por conversa (FinOps) e mudança de prompt passa pela suíte."),
(25,"etapa-20-governanca","etapa","Execute a Etapa 20 (governança da IA): ai-logs higienizados com scan, 100% dos PRs com revisão humana e SBOM com licenças."),
(26,"etapa-21-retro","etapa","Execute a Etapa 21 (retrospectivas e postmortems): postmortem sem culpa em 48h com action items como tickets e DORA acompanhado por release."),
(27,"checklist-22-portoes","etapa","Percorra o checklist final dos 22 portões antes de implantar e me avise se faltar alguma etapa do guia."),
(28,"push-github","decisao","Envie o projeto para este repositório Git; o padrão de commit será definido por mim: git@github.com:edijrcompany-source/namastexlab.git"),
(29,"ssh-registrada","validacao","Feito — a chave SSH foi registrada; prossiga com o push."),
(30,"desenvolvimento-tdd","goal","Seguindo TDD e cobertura total de testes unitários, revise toda a documentação, gere o documento de implementações com escopo imutável e inicie o desenvolvimento com a arquitetura planejada."),
(31,"confirmar-stack","duvida","Confirme: front e back estão considerados? Qual a stack e as ferramentas de CI/CD, mensageria e observabilidade?"),
(32,"status-infra","duvida","Essa infraestrutura já está desenvolvida ou apenas planejada?"),
(33,"seguir-t03","goal","Continue o desenvolvimento conforme a arquitetura e o cronograma, com 100% de cobertura de testes unitários e Playwright."),
(34,"goal-finalizar","goal","Siga a documentação até finalizar todo o projeto; suba os containers ou o que for necessário para eu rodar e testar, com cobertura total de testes, seguindo toda a arquitetura planejada."),
(35,"reboot-concluido","validacao","Reinício concluído — pode continuar com o objetivo."),
(36,"bug-loop","bug","Encontramos o primeiro bug: o agente está repetindo a pergunta do veículo em loop. Investigue a causa seguindo o padrão de engenharia, corrija e aplique testes em todas as chamadas de API para validar que todas as APIs do desafio funcionam."),
(37,"reset-portas","bug","Encerre todos os processos locais e reergua o ambiente — as portas estão conflitando e refletindo plataformas erradas."),
(38,"checagem-engine","automacao","Verificação agendada: se o Docker engine subiu, executar o compose e validar o health; caso contrário, encerrar em silêncio."),
(39,"virtualizacao","duvida","O Docker Desktop reporta ausência de suporte à virtualização. Preciso ativar a virtualização?"),
(40,"certificacao-final","goal","Complete o ciclo: acrescente ao guia os capítulos de entrega modular com Scrum e normas de segurança (OAuth 2.1+PKCE, RBAC, RLS, rate limiting, DTO, OWASP); explique e registre os ai-logs; audite 100% dos requisitos do desafio; certifique a execução; e registre todos os prompts desta sessão (refinados, com timestamp e um commit por prompt)."),
]

os.makedirs("ai-logs/prompts", exist_ok=True)
for num, slug, cat, texto in P:
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    base = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    arq = f"ai-logs/prompts/p{num:02d}-{slug}.md"
    io.open(arq, "w", encoding="utf-8", newline="\n").write(
        f"""---
n: {num}
quando: {agora}  (base: {base})
categoria: {cat}
---

## Prompt (refinado)

{texto}

## Resultado

Registrado no log incremental; ver commit deste arquivo e o índice em prompts/README.md.
"""
    )
    subprocess.run(["git", "add", arq], check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", f"docs(ai-logs): register prompt p{num:02d} ({slug})"],
        check=True,
    )
print("OK", len(P), "prompts registrados")
