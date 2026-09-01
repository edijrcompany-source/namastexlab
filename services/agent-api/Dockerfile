# syntax=docker/dockerfile:1.7
##############################################################################
# agent-api — imagem ÚNICA multi-destino (dev compose = Railway = VPS)
# CONTEXTO DE BUILD: RAIZ DO REPO (compose: context ".") — messages/ e prompts/
# vivem na raiz e entram na imagem (autocontida). Multi-stage · não-root.
##############################################################################

########## Stage 1 — builder ##########
FROM python:3.12-slim AS builder

ENV UV_PYTHON_DOWNLOADS=never     UV_LINK_MODE=copy     UV_PROJECT_ENVIRONMENT=/build/.venv

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /build
COPY services/agent-api/pyproject.toml services/agent-api/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev

COPY services/agent-api/app ./app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

########## Stage 2 — runtime ##########
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PATH="/app/.venv/bin:$PATH"     APP_HOME=/app

# usuário dedicado não-root (Etapa 15)
RUN groupadd --gid 10001 app     && useradd --uid 10001 --gid app --shell /usr/sbin/nologin --create-home app

WORKDIR ${APP_HOME}

COPY --from=builder --chown=app:app /build/.venv ${APP_HOME}/.venv
COPY --chown=app:app services/agent-api/app ${APP_HOME}/app
COPY --chown=app:app messages ${APP_HOME}/messages
COPY --chown=app:app prompts ${APP_HOME}/prompts

USER app:app

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=4s --start-period=10s --retries=3     CMD ["python", "-c", "import sys,httpx;sys.exit(0 if httpx.get('http://127.0.0.1:8001/health',timeout=3).status_code==200 else 1)"]

# python -m: shebangs do venv apontam p/ /build (builder) — -m é imune a isso
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
