# Módulo versionado: stack completa do AutoSeguro num ambiente Railway.
# Mesma forma para staging e produção (Etapa 17 §1) — só parâmetros mudam.
# CHANGELOG: 0.1.0 (2026-09-01) — spec inicial declarativa (adoção valida providers).
terraform {
  required_version = ">= 1.8"
  required_providers {
    railway = {
      source  = "railwayzx/railway"
      version = "~> 3.0"
    }
  }
}

variable "env_name" {
  description = "Nome do ambiente (staging | production)"
  type        = string
}

variable "github_repo" {
  description = "repo GitHub para imagem GHCR (owner/repo)"
  type        = string
}

variable "agent_api_image" {
  description = "Imagem única multi-destino (Etapa 15) — mesma em todos os envs"
  type        = string
}

variable "seed_sintetico" {
  description = "staging carrega seed Silver fixture; produção nunca"
  type        = bool
  default     = false
}

resource "railway_project" "this" {
  name = "namastex-fde-${var.env_name}"
}

# ── agent-api (nossa imagem GHCR — nunca segredos no state, só referências) ──
resource "railway_service" "agent_api" {
  project_id = railway_project.this.id
  name       = "agent-api"
  # imagem publicada pelo release.yml (tag sha) — multi-destino por construção
}

resource "railway_variable" "agent_api_common" {
  project_id = railway_project.this.id
  service_id = railway_service.agent_api.id
  # chaves IDENTICAS em todos os ambientes (spec §9); valores por ambiente
  variables = {
    QUOTE_API_URL      = "http://quote-api.railway.internal:8000"
    QUOTE_TIMEOUT_MS   = "3000"
    QUOTE_MAX_ATTEMPTS = "3"
    CB_THRESHOLD       = "5"
    CB_COOLDOWN_S      = "30"
    CB_SUCCESSES_TO_CLOSE = "2"
    MASKING_STRICT     = "true"
    LOG_LEVEL          = var.env_name == "production" ? "INFO" : "DEBUG"
    DATABASE_URL       = "${railway_service.postgres.database_url}" # injetado pelo Railway
    # LLM_API_KEY / ADMIN_TOKEN: NÃO estão aqui — cofre por ambiente (etapa-17 §4)
  }
}

# ── quote-api (Dockerfile DO DESAFIO — intocado, regra 3) ──
resource "railway_service" "quote_api" {
  project_id = railway_project.this.id
  name       = "quote-api"
  source = {
    repo = var.github_repo
    root_directory = "quote-service"
  }
}

resource "railway_variable" "quote_api_instabilidade" {
  project_id = railway_project.this.id
  service_id = railway_service.quote_api.id
  variables = {
    QUOTE_FAILURE_RATE = "0.20" # a instabilidade É o produto (spec §2)
    QUOTE_SLOW_RATE    = "0.10"
    QUOTE_SLOW_SECONDS = "8"
    # QUOTE_SEED: vazio em prod (probabilístico real); 42 em e2e local
  }
}

# ── Postgres ──
resource "railway_service" "postgres" {
  project_id = railway_project.this.id
  name       = "postgres"
}

output "project_id" { value = railway_project.this.id }
