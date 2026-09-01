"""Fábrica da app FastAPI — monta as bordas (routers)."""

from fastapi import FastAPI

from app.api.conversations import router as conversations_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(title="AutoSeguro agent-api", version="0.1.0")
    application.include_router(health_router)
    application.include_router(conversations_router)
    return application


app = create_app()
