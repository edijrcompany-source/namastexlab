"""Fábrica da app FastAPI — monta as bordas (routers) + CORS (origem exata)."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.conversations import router as conversations_router
from app.api.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(title="AutoSeguro agent-api", version="0.1.0")
    application.include_router(health_router)
    application.include_router(conversations_router)
    origins = [
        o.strip()
        for o in os.getenv("AGENT_CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # origem EXATA (T16) — nunca "*"
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Correlation-Id", "Idempotency-Key", "Authorization"],
    )
    return application


app = create_app()
