"""Wiring — monta o orchestrator por env (spec §9 + ADR-0005).

Padrões: sem LLM_API_KEY ⇒ FakeLLM (offline, determinístico — modo demo/avaliador);
com chave ⇒ OpenAI gpt-4o-mini. A ACL sempre é real (aponta o quote-api).
"""

from __future__ import annotations

import os

from app.conversation.orchestrator import TurnOrchestrator
from app.domain.ports import LLMPort
from app.llm.fake import FakeLLM
from app.quoting.client import QuoteAcl, QuoteAclConfig


def construir_llm() -> LLMPort:
    from app.llm.openai_client import OpenAIClient

    chave = os.getenv("LLM_API_KEY", "")
    if chave:
        return OpenAIClient(api_key=chave, model=os.getenv("LLM_MODEL", "gpt-4o-mini"))
    return FakeLLM()


def construir_acl() -> QuoteAcl:
    return QuoteAcl(
        base_url=os.getenv("QUOTE_API_URL", "http://localhost:8000"),
        config=QuoteAclConfig.from_env(),
    )


_ORCHESTRATOR: TurnOrchestrator | None = None


def obter_orchestrator() -> TurnOrchestrator:
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = TurnOrchestrator(llm=construir_llm(), acl=construir_acl())
    return _ORCHESTRATOR
