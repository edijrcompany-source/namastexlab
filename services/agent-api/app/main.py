"""Fábrica da app FastAPI — monta as bordas (routers) + CORS + correlation middleware."""

import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.conversations import router as conversations_router
from app.api.health import router as health_router
from app.observability import get_logger, set_correlation_id

log = get_logger("agent-api.http")


def create_app() -> FastAPI:
    application = FastAPI(title="AutoSeguro agent-api", version="0.1.0")

    @application.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        """Correlation_id em TODO request + log de acesso estruturado (Etapa 18 §1)."""
        cid = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        set_correlation_id(cid)
        inicio = time.perf_counter()
        response = await call_next(request)
        duracao_ms = round((time.perf_counter() - inicio) * 1000, 1)
        log.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duracao_ms": duracao_ms,
            },
        )
        response.headers["X-Correlation-Id"] = cid
        return response

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
