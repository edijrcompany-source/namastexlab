"""OpenAI client — LLMPort real (ADR-0005: default gpt-4o-mini, JSON mode).

Usado SOMENTE quando LLM_API_KEY está presente; sem chave o wiring usa FakeLLM
(o sistema inteiro roda offline — inclusive a demo do avaliador).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from app.llm.extraction import Campos
from app.llm.port import TurnoLLM


def _system_prompt(caminhos_extra: list | None = None) -> str:
    if caminhos_extra is not None:  # injeção total (teste do fallback)
        caminhos = caminhos_extra
    else:
        caminhos = [
            Path(os.getenv("PROMPTS_PATH", "")) if os.getenv("PROMPTS_PATH") else None,
            Path("/app/prompts/system_v1.md"),
            Path(__file__).resolve().parents[4] / "prompts" / "system_v1.md",
        ]
    for caminho in caminhos:
        if caminho and caminho.exists():
            return caminho.read_text(encoding="utf-8")
    return (
        "Você é o atendente da AutoSeguro. Responda APENAS com JSON "
        '{"intent","dados_extraidos","campos_corrigidos","resposta"}. '
        "Nunca cite valores que não estejam em contexto.cotacoes."
    )


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        http: httpx.Client | None = None,
    ) -> None:
        self._key = api_key
        self._model = model
        self._base = base_url
        self._http = http or httpx.Client(timeout=15.0)

    def completar(
        self,
        *,
        estado: str,
        dados: Campos,
        historico: list[str],
        mensagem: str,
        aviso_correcao: bool = False,
    ) -> TurnoLLM:
        from app.llm.extraction import Campos as _Campos

        dados = dados or _Campos()  # porta tolera ausência (mesma semântica do FakeLLM)
        user = json.dumps(
            {
                "estado": estado,
                "dados": {
                    "veiculo_texto": dados.veiculo_texto,
                    "veiculo_ano": dados.veiculo_ano,
                    "idade": dados.idade,
                    "cep": dados.cep,
                },
                "historico": historico,
                "mensagem": mensagem,
                **(
                    {"aviso": "resposta anterior citou preço sem origem; corrija"}
                    if aviso_correcao
                    else {}
                ),
            },
            ensure_ascii=False,
        )
        resp = self._http.post(
            f"{self._base}/chat/completions",
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "model": self._model,
                "temperature": 0.2,
                "max_tokens": 500,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": _system_prompt()},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        corpo = json.loads(resp.json()["choices"][0]["message"]["content"])
        campos = Campos(
            veiculo_texto=corpo.get("dados_extraidos", {}).get("veiculo_texto"),
            veiculo_ano=corpo.get("dados_extraidos", {}).get("veiculo_ano"),
            idade=corpo.get("dados_extraidos", {}).get("idade"),
            cep=corpo.get("dados_extraidos", {}).get("cep"),
            data_inicio=corpo.get("dados_extraidos", {}).get("data_inicio"),
        )
        return TurnoLLM(corpo.get("intent", "outro"), corpo.get("resposta", ""), campos)
