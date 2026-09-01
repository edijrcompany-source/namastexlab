# AMBIENTE: staging — espelha produção (mesmo módulo, escala mínima, seed sintético).
# Mudança de infra só via PR com plan revisado (infra.yml — Etapa 17 §3).
terraform {
  required_version = ">= 1.8"
  required_providers {
    railway = {
      source  = "railwayzx/railway"
      version = "~> 3.0"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }
}

module "stack" {
  source          = "../../modules/railway-stack"
  env_name        = "staging"
  github_repo     = "namastex-lab/namastex-fde"
  agent_api_image = "ghcr.io/namastex-lab/namastex-fde/agent-api:main" # trailing main
  seed_sintetico  = true # staging SEMPRE com dados sintéticos (nunca PII real)
}

# front: preview estável de staging na Vercel (produção promove por integração)
resource "vercel_project" "web" {
  name      = "namastex-fde-web"
  framework = "nextjs"
  git_repository = {
    type = "github"
    repo = "namastex-lab/namastex-fde"
  }
}

resource "vercel_project_domain" "staging" {
  project_id = vercel_project.web.id
  domain     = "staging-namastex-fde.vercel.app"
}
