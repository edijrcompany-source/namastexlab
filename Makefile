# Makefile — linguagem comum de humano, agente e CI (ADR-0011)
# Alvos ainda não implementados FALHAM com a task responsável (nunca silenciosamente).

.PHONY: help contracts-lint codegen codegen-check mock dev bronze silver test evals fmt lint pseudo-locale docs-dev docs-build docs-api storybook

help: ## lista os alvos
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

contracts-lint: ## spectral nos contratos OpenAPI (blocker — Etapa 5)
	pnpm dlx @stoplight/spectral-cli lint openapi/*.yaml

codegen: ## gera types TS do contrato (apps/web/src/types/api.d.ts)
	pnpm dlx openapi-typescript openapi/agent-api.yaml -o apps/web/src/types/api.d.ts

codegen-check: codegen ## falha se alguém editou types gerados à mão
	git diff --exit-code apps/web/src/types/api.d.ts || (echo "TYPES GERADOS FORAM EDITADOS/DESATUALIZADOS — rode 'make codegen' e commite" && exit 1)

mock: ## Prism mock do agent-api em :4010 (front anda sem back)
	pnpm dlx @stoplight/prism-cli mock openapi/agent-api.yaml -p 4010

dev: ## sobe ambiente completo (compose) — agent-api requer app/ do T-01
	docker compose up --build

dev-deps: ## sobe SO dependencias ja disponiveis: postgres + quote-api
	docker compose up postgres quote-api

dev-e2e: ## compose com legado DETERMINISTICO (QUOTE_SEED=42) p/ e2e C4/C5
	QUOTE_SEED=42 docker compose up --build

migrate: ## roda alembic upgrade head (job efemero do compose)
	docker compose run --rm migrations

lint-docker: ## hadolint no Dockerfile do agent-api (quote-service nao e nosso)
	pnpm dlx hadolint services/agent-api/Dockerfile

scan: ## trivy na imagem — CVE CRITICA/HIGH = falha (portao Etapa 15)
	docker build -t agent-api:scan services/agent-api
	trivy image --exit-code 1 --severity CRITICAL,HIGH agent-api:scan

bronze: ## regenera dataset Bronze (seed 42, gerador do desafio) — T-08
	CHALLENGE="$${NAMASTEX_CHALLENGE_DIR:-../namastex-fde-challenge}"; 	uv run --with pandas --with pyarrow python "$$CHALLENGE/scripts/generate_dataset.py" 		--n 2500 --seed 42 --out dataset/conversations.parquet

silver: ## Bronze -> Silver: masking §3 + normalização + relatório (spec §7) — T-08
	uv run --project scripts python scripts/build_silver.py 		--bronze dataset/conversations.parquet --silver dataset/silver/conversations.parquet

test-data: ## testes do pipeline de dados (scripts/tests)
	cd scripts && uv run --group dev pytest tests/ -q

test: ## pytest + coverage gate >=90% (logica deterministica) — Etapa 14
	@echo "ERRO: alvo 'test' chega com a Etapa 14 (tests/ em services/agent-api)."; exit 1

evals: ## suite de evals (extracao, handoff, 20 ataques) — Etapa 19
	@echo "ERRO: alvo 'evals' chega com a Etapa 19 (evals/)."; exit 1

fmt: ## ruff format + ruff --fix + prettier --write (Etapa 13)
	cd services/agent-api && uv run ruff format . && uv run ruff check --fix .
	pnpm exec prettier apps/web --write

lint: ## ruff + eslint --max-warnings 0 + import-linter + pre-commit all (Etapa 13 — catraca)
	cd services/agent-api && uv run ruff check . && uv run ruff format --check . && uv run lint-imports
	pnpm exec eslint apps/web --max-warnings 0
	pre-commit run --all-files

pseudo-locale: ## gera + valida pseudo-locale pt-X-TEST — Etapa 7 (6)
	@echo "ERRO: alvo 'pseudo-locale' chega com os scripts/ da Etapa 7."; exit 1

docs-dev: ## portal de docs em modo dev (VitePress :5173) — Etapa 12
	pnpm dlx vitepress dev docs

docs-build: ## build do portal (saida docs/.vitepress/dist) — publicado pelo CI (Etapa 16)
	pnpm dlx vitepress build docs

docs-api: ## renderiza Redoc dos contratos (referencia de API gerada, nunca a mao)
	pnpm dlx @redocly/cli build-docs openapi/agent-api.yaml -o docs/public/api-agent.html
	pnpm dlx @redocly/cli build-docs openapi/quote-api.yaml -o docs/public/api-quote.html

storybook: ## catalogo vivo de componentes (nasce com o front — T-11)
	@echo "ERRO: storybook chega com a task T-11 (apps/web)."; exit 1

test-e2e: ## E2E C1-C6 contra o compose (noturno/pre-release — Etapa 14)
	@echo "ERRO: e2e precisa do front (T-11) + compose e2e (QUOTE_SEED=42)."; exit 1

test-mutation: ## mutmut no nucleo py (score >=60% — noturno — Etapa 14)
	cd services/agent-api && uv run mutmut run --paths-to-mutate app/conversation app/privacy app/quoting

smoke: ## smoke pos-deploy (demo real) — Etapa 14
	cd e2e && pnpm exec playwright test smoke.spec.ts

sbom: ## inventario SBOM + licencças (syft — Etapa 20)
	syft dir:services/agent-api -o spdx-json > sbom-agent-api.json
	syft dir:apps/web -o spdx-json > sbom-web.json
	@echo "OK — verificar licenças contra a allowlist (Etapa 20 §4)"
