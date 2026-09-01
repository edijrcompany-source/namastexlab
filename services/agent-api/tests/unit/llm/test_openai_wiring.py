"""OpenAIClient (mock transport) + wiring deps — 100% da camada LLM real."""

import json

import httpx
import pytest

import app.api.deps as deps
from app.api.deps import construir_acl, construir_llm, obter_orchestrator
from app.llm.fake import FakeLLM
from app.llm.openai_client import OpenAIClient


def _transport_ok(request: httpx.Request) -> httpx.Response:
    corpo = json.loads(request.content)
    assert corpo["response_format"] == {"type": "json_object"}  # spec §4.1
    assert corpo["temperature"] == 0.2
    turno = {
        "intent": "informa_dados",
        "dados_extraidos": {"veiculo_ano": 2022, "idade": 30, "cep": "01310-100"},
        "campos_corrigidos": {},
        "resposta": "Anotado!",
    }
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": json.dumps(turno, ensure_ascii=False)}}]},
    )


@pytest.mark.unit
def test_openai_client_sucesso_com_mock() -> None:
    client = OpenAIClient(
        api_key="k", http=httpx.Client(transport=httpx.MockTransport(_transport_ok))
    )
    turno = client.completar(estado="QUALIFICANDO", dados=None, historico=[], mensagem="onix 2022")
    assert turno.intent == "informa_dados"
    assert turno.campos.veiculo_ano == 2022
    assert turno.resposta == "Anotado!"


@pytest.mark.unit
def test_openai_client_aviso_correcao_no_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        user = json.loads(json.loads(request.content)["messages"][1]["content"])
        assert user.get("aviso", "").startswith("resposta anterior")
        turno = {"intent": "outro", "dados_extraidos": {}, "resposta": "ok"}
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(turno)}}]})

    client = OpenAIClient(api_key="k", http=httpx.Client(transport=httpx.MockTransport(handler)))
    turno = client.completar(
        estado="QUALIFICANDO", dados=None, historico=[], mensagem="x", aviso_correcao=True
    )
    assert turno.intent == "outro"


@pytest.mark.unit
def test_wiring_sem_chave_usa_fakellm(monkeypatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert isinstance(construir_llm(), FakeLLM)


@pytest.mark.unit
def test_wiring_com_chave_usa_openai(monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "sk-teste")
    assert isinstance(construir_llm(), OpenAIClient)


@pytest.mark.unit
def test_wiring_acl_por_env(monkeypatch) -> None:
    monkeypatch.setenv("QUOTE_API_URL", "http://legado:9000")
    monkeypatch.setenv("QUOTE_TIMEOUT_MS", "1500")
    acl = construir_acl()
    assert acl._base_url == "http://legado:9000"
    assert acl._config.timeout_ms == 1500


@pytest.mark.unit
def test_singleton_do_orchestrator(monkeypatch) -> None:
    deps._ORCHESTRATOR = None
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    primeiro = obter_orchestrator()
    assert obter_orchestrator() is primeiro  # singleton (spec §9)
    deps._ORCHESTRATOR = None


@pytest.mark.unit
def test_system_prompt_fallback_quando_nenhum_arquivo_existe() -> None:
    from app.llm.openai_client import _system_prompt

    prompt = _system_prompt(caminhos_extra=[])
    assert "APENAS com JSON" in prompt  # fallback embutido (sem arquivo de prompt)


@pytest.mark.unit
def test_system_prompt_carrega_o_arquivo_real_do_repo() -> None:
    from app.llm.openai_client import _system_prompt

    prompt = _system_prompt()  # caminhos padrão: repo/container
    assert "INVIOLÁVEIS" in prompt  # prompts/system_v1.md
