"""Contrato do /health (openapi/agent-api.yaml §/health + spec §5.4)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
def test_health_retorna_o_contrato() -> None:
    resp = TestClient(app).get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "ok"
    assert body["legado"] in ("ok", "degradado")
    assert body["versao"] == "0.1.0"


@pytest.mark.integration
def test_health_tem_content_type_json() -> None:
    resp = TestClient(app).get("/health")

    assert resp.headers["content-type"].startswith("application/json")
