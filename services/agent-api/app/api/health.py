"""GET /health — saúde do agente e do legado (contrato: openapi/agent-api.yaml)."""

from fastapi import APIRouter

router = APIRouter()

VERSAO = "0.1.0"


@router.get("/health")
def health() -> dict[str, str]:
    # TODO(T-07): ping real do quote-api cacheado 30s ("degradado" quando fora).
    # Por ora o legado é considerado ok (scaffold) — o shape do contrato já é o final.
    return {"agent": "ok", "legado": "ok", "versao": VERSAO}
