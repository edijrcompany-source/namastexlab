# syntax=docker/dockerfile:1.7
##############################################################################
# agent-api — imagem ÚNICA multi-destino (dev compose = Railway = VPS — ADR-0011/0008)
# Multi-stage · base slim · processo NÃO-ROOT (Etapa 15 / portão)
# Hadolint-clean (ver .hadolint.yaml na raiz) · CVE gate: `make scan` (Trivy)
##############################################################################

########## Stage 1 — builder (ferramentas de build ficam aqui) ##########
FROM python:3.12-slim AS builder

ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/build/.venv

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /build
# Camadas de dependência primeiro (cache): lock é a fonte (uv.lock chega com T-01)
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev

# Código da aplicação (nasce no T-01 — até lá o build falha apontando a task)
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

########## Stage 2 — runtime (mínimo, sem ferramentas de build) ##########
FROM python:3.12-slim AS runtime

# hadolint: sem apt — nada a instalar; base slim intencional
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    APP_HOME=/app

# Usar usuário dedicado não-root (portão da Etapa 15)
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --shell /usr/sbin/nologin --create-home app

WORKDIR ${APP_HOME}

# venv do builder + código + artefatos de design que a app LÊ em runtime:
COPY --from=builder --chown=app:app /build/.venv ${APP_HOME}/.venv
COPY --chown=app:app app ${APP_HOME}/app
COPY --chown=app:app messages ${APP_HOME}/messages   # catálogo i18n (ADR-0009)
COPY --chown=app:app prompts ${APP_HOME}/prompts     # system_v1.md (Etapa 20)

USER app:app

EXPOSE 8001

# healthcheck sem curl/wget (slim): httpx já é dependência da app
HEALTHCHECK --interval=15s --timeout=4s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os,sys,httpx;sys.exit(0 if httpx.get('http://127.0.0.1:8001/health',timeout=3).status_code==200 else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
