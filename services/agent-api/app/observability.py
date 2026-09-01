"""Observabilidade — logging JSON estruturado (Etapa 18 §1).

Toda saída de log é JSON com: correlation_id, conversation_id, evento, ts.
PII mascarada por construction (spec §3) — o masking roda ANTES do log.
Uso: from app.observability import get_logger; log = get_logger(); log.info("quote_ok", ...)
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")
_conversation_id: ContextVar[str] = ContextVar("conversation_id", default="-")


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def set_conversation_id(cid: str) -> None:
    _conversation_id.set(cid)


class StructuredFormatter(logging.Formatter):
    """JSON por linha — Loki/Datadog/Railey inguem nativo."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                "level": record.levelname.lower(),
                "msg": record.getMessage(),
                "correlation_id": _correlation_id.get(),
                "conversation_id": _conversation_id.get(),
                "module": record.module,
                "func": record.funcName,
                **(getattr(record, "extra_fields", {})),
            },
            ensure_ascii=False,
        )


def get_logger(name: str = "agent-api") -> logging.Logger:
    """Logger estruturado singleton — stdout JSON, sem PII."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
