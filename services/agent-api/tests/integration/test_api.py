"""API HTTP de ponta a ponta — contrato openapi/agent-api.yaml (spec §5.4).

C1 inteiro via HTTP + erros do catálogo + export + handoffs + LGPD delete.
"""

import pytest
from fastapi.testclient import TestClient

from app.conversation.orchestrator import TurnOrchestrator
from app.main import app
from tests.unit.conversation.test_orchestrator import StubACL


@pytest.fixture()
def cliente():
    """App com ACL stub (sem legado) para HTTP tests determinísticos."""
    global _ORCHESTRATOR
    import app.api.deps as deps

    deps._ORCHESTRATOR = TurnOrchestrator(llm=deps.construir_llm(), acl=StubACL())
    with TestClient(app) as client:
        yield client
    deps._ORCHESTRATOR = None


@pytest.mark.integration
def test_c1_completo_por_http(cliente: TestClient) -> None:
    # 1. cria conversa
    r = cliente.post(
        "/conversations", headers={"X-Correlation-Id": "11111111-1111-1111-1111-111111111111"}
    )
    assert r.status_code == 201
    conv_id = r.json()["conversation_id"]
    assert r.json()["estado"] == "QUALIFICANDO"

    # 2. qualifica
    r = cliente.post(
        f"/conversations/{conv_id}/messages", json={"text": "Onix 2022, 30 anos, CEP 01310-100"}
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "CONFIRMANDO"

    # 3. confirma → cotação (stub)
    r = cliente.post(f"/conversations/{conv_id}/messages", json={"text": "é isso"})
    body = r.json()
    assert body["estado"] == "COTACAO_APRESENTADA"
    assert body["cotacao"]["premio_mensal"] == 155.87
    assert "R$ 155,87" in body["reply"]["texto"]

    # 4. aceite → handoff
    r = cliente.post(f"/conversations/{conv_id}/messages", json={"text": "fechado!"})
    body = r.json()
    assert body["estado"] == "HANDOFF"
    assert body["handoff"]["motivo"] == "aceite_fechamento"

    # 5. timeline + export + fila
    tl = cliente.get(f"/conversations/{conv_id}")
    assert tl.status_code == 200
    assert tl.json()["handoff"]["motivo"] == "aceite_fechamento"
    assert any(e["type"] == "quote_succeeded" for e in tl.json()["eventos"])

    md = cliente.get(f"/conversations/{conv_id}/export?fmt=md")
    assert md.status_code == 200
    assert "text/markdown" in md.headers["content-type"]
    assert "R$ 155,87" in md.text

    fila = cliente.get("/handoffs")
    assert fila.status_code == 200
    assert fila.json()["items"][0]["motivo"] == "aceite_fechamento"


@pytest.mark.integration
def test_404_conversa_inexistente(cliente: TestClient) -> None:
    r = cliente.get("/conversations/01J8Z9C3K5M7P9R2T4V6W8YBAA")
    assert r.status_code == 404
    assert "Não achamos" in r.json()["detail"]


@pytest.mark.integration
def test_422_text_e_midia_juntos(cliente: TestClient) -> None:
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    r = cliente.post(
        f"/conversations/{conv_id}/messages",
        json={"text": "oi", "media_type": "image", "media_marker": "[imagem] x"},
    )
    assert r.status_code == 422


@pytest.mark.integration
def test_midia_por_http(cliente: TestClient) -> None:
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    r = cliente.post(
        f"/conversations/{conv_id}/messages",
        json={"media_type": "document", "media_marker": "[documento] CNH.pdf"},
    )
    assert r.status_code == 200
    assert "escrever" in r.json()["reply"]["texto"]


@pytest.mark.integration
def test_delete_lgpd_com_token(cliente: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_TOKEN", "segredo")
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    assert cliente.delete(f"/conversations/{conv_id}").status_code == 401  # sem token
    ok = cliente.delete(f"/conversations/{conv_id}", headers={"Authorization": "Bearer segredo"})
    assert ok.status_code == 204
    assert cliente.get(f"/conversations/{conv_id}").status_code == 404


@pytest.mark.integration
def test_export_fmt_json_e_timeline_sem_dados(cliente: TestClient) -> None:
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    export = cliente.get(f"/conversations/{conv_id}/export?fmt=json")
    assert export.status_code == 200
    assert export.json()["dados_qualificados"] is None  # sem dados mascarados


@pytest.mark.integration
def test_422_corpo_vazio(cliente: TestClient) -> None:
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    r = cliente.post(f"/conversations/{conv_id}/messages", json={})
    assert r.status_code == 422


@pytest.mark.integration
def test_mascara_cep_nos_dados_qualificados(cliente: TestClient) -> None:
    r = cliente.post("/conversations")
    conv_id = r.json()["conversation_id"]
    cliente.post(f"/conversations/{conv_id}/messages", json={"text": "tenho 30 anos"})
    tl = cliente.get(f"/conversations/{conv_id}").json()
    assert tl["dados_qualificados"] == {
        "veiculo_texto": None,
        "veiculo_ano": None,
        "idade": 30,
        "cep": None,
    }
