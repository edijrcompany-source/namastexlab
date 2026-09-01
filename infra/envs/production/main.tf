# AMBIENTE: produção (demo pública) — mesmo módulo do staging, sem seed.
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
  env_name        = "production"
  github_repo     = "namastex-lab/namastex-fde"
  agent_api_image = "ghcr.io/namastex-lab/namastex-fde/agent-api:latest" # release.yml faz rollback por tag sha (LAST_GOOD_TAG)
  seed_sintetico  = false
}

resource "vercel_project" "web" {
  name      = "namastex-fde-web"
  framework = "nextjs"
  git_repository = {
    type = "github"
    repo = "namastex-lab/namastex-fde"
  }
}

resource "vercel_project_domain" "production" {
  project_id = vercel_project.web.id
  domain     = "namastex-fde.vercel.app"
}
