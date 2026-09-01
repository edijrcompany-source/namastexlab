"""Endpoints de conversa — contrato openapi/agent-api.yaml §paths (spec §5.4)."""

from __future__ import annotations

import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field

from app.api.deps import obter_orchestrator
from app.conversation.models import Conversa
from app.events.store import Store
from app.i18n import carregar, t
from app.observability import get_logger, set_conversation_id, set_correlation_id

router = APIRouter()
log = get_logger(__name__)


class MensagemIn(BaseModel):
    text: str | None = Field(default=None, max_length=4000)
    media_type: str | None = None
    media_marker: str | None = Field(default=None, max_length=200)


def _catalogo() -> dict:
    return carregar()


def _erro(slug: str) -> dict:
    """title/detail do catálogo api.erro.<slug> (chave = código estável §6)."""
    return _catalogo()["api"]["erro"][slug]


def _store() -> Store:
    return obter_orchestrator().store


def _obter_ou_404(conversation_id: str) -> Conversa:
    conversa = _store().obter(conversation_id)
    if conversa is None:
        raise HTTPException(status_code=404, detail=_erro("conversa_nao_encontrada")["detail"])
    return conversa


@router.post("/conversations", status_code=201)
def criar_conversa(
    x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-Id")] = None,
) -> dict:
    orch = obter_orchestrator()
    correlation = x_correlation_id or str(uuid.uuid4())
    set_correlation_id(correlation)
    conversa = orch.iniciar(correlation_id=correlation)
    set_conversation_id(conversa.id)
    log.info("conversation_started", extra={"conversation_id": conversa.id})
    return {
        "conversation_id": conversa.id,
        "estado": conversa.estado.value,
        "criada_em": conversa.criada_em.isoformat(),
    }


@router.post("/conversations/{conversation_id}/messages")
def enviar_mensagem(
    conversation_id: str,
    corpo: MensagemIn,
    x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-Id")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict:
    orch = obter_orchestrator()
    _obter_ou_404(conversation_id)  # 404 antes de validar corpo
    if corpo.text and (corpo.media_type or corpo.media_marker):
        raise HTTPException(status_code=422, detail=_erro("payload_invalido")["detail"])
    if not corpo.text and not (corpo.media_type and corpo.media_marker):
        raise HTTPException(status_code=422, detail=_erro("payload_invalido")["detail"])

    orch = obter_orchestrator()
    if corpo.text is not None:
        conversa = orch.processar(conversation_id, texto=corpo.text)
    else:
        conversa = orch.processar(conversation_id, midia=(corpo.media_type, corpo.media_marker))
    resposta = conversa.historico[-1]
    corpo_resposta = {
        "conversation_id": conversa.id,
        "estado": conversa.estado.value,
        "reply": {
            "role": resposta.role,
            "tipo": resposta.tipo,
            "texto": resposta.texto,
            "criado_em": resposta.criado_em.isoformat(),
        },
        "eventos": conversa.eventos[-6:],
        "cotacao": conversa.cotacoes[-1] if conversa.cotacoes else None,
        "handoff": conversa.handoff,
    }
    return corpo_resposta


@router.get("/conversations/{conversation_id}")
def timeline(conversation_id: str) -> dict:
    conversa = _obter_ou_404(conversation_id)
    dados = conversa.dados
    return {
        "conversation_id": conversa.id,
        "estado": conversa.estado.value,
        "dados_qualificados": {
            "veiculo_texto": dados.veiculo_texto,
            "veiculo_ano": dados.veiculo_ano,
            "idade": dados.idade,
            "cep": _mascara_cep(dados.cep),
        }
        if dados.veiculo_ano or dados.idade or dados.cep
        else None,
        "mensagens": [
            {
                "role": m.role,
                "tipo": m.tipo,
                "texto": m.texto,
                "criado_em": m.criado_em.isoformat(),
            }
            for m in conversa.historico
        ],
        "eventos": conversa.eventos,
        "cotacoes": conversa.cotacoes,
        "handoff": conversa.handoff,
        "criada_em": conversa.criada_em.isoformat(),
        "atualizada_em": conversa.atualizada_em.isoformat(),
    }


@router.get("/conversations/{conversation_id}/export", response_model=None)
def exportar(conversation_id: str, fmt: str = "json") -> Response | dict:
    conversa = _obter_ou_404(conversation_id)
    if fmt == "md":
        catalogo = _catalogo()
        linhas = [f"# Conversa {conversa.id}", ""]
        for m in conversa.historico:
            quem = "Lead" if m.role == "lead" else "Agente"
            linhas.append(f"**{quem}**: {m.texto}")
            linhas.append("")
        linhas.append("## Eventos")
        for e in conversa.eventos:
            linhas.append(f"- `{e['seq']}` **{e['type']}** {e['payload']}")
        if conversa.handoff:
            linhas.append(f"\n> Handoff: **{conversa.handoff['motivo']}**")
        correlation = conversa.correlation_id or "—"
        rodape = t("ui.chat.correlation_rodape", catalogo, correlation_id=correlation)
        linhas.append(f"\n{rodape}")
        return Response(content="\n".join(linhas), media_type="text/markdown")
    return timeline(conversation_id)


@router.get("/handoffs")
def handoffs() -> dict:
    pendentes = _store().handoffs_pendentes()
    return {
        "items": [
            {
                "id": c.handoff["id"],
                "conversation_id": c.id,
                "motivo": c.handoff["motivo"],
                "resumo": c.handoff["resumo"],
                "criado_em": c.atualizada_em.isoformat(),
                "status": c.handoff["status"],
            }
            for c in pendentes
        ]
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
def apagar(
    conversation_id: str,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    _obter_ou_404(conversation_id)
    token = os.getenv("ADMIN_TOKEN", "")
    enviado = (authorization or "").removeprefix("Bearer ").strip()
    if not token or enviado != token:
        raise HTTPException(status_code=401, detail=_erro("nao_autorizado")["detail"])
    _store().apagar(conversation_id)
    return Response(status_code=204)


def _mascara_cep(cep: str | None) -> str | None:
    if not cep:
        return None
    return f"{cep[:2]}***-***"
