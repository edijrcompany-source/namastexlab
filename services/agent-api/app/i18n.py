"""Catálogo i18n — loader do messages/pt-BR.json (ADR-0009: fonte única)."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _caminho_catalogo() -> Path:
    env = os.getenv("MESSAGES_PATH")
    if env:
        return Path(env)
    container = Path("/app/messages/pt-BR.json")
    if container.exists():  # pragma: no cover — só existe dentro do container
        return container
    return Path(__file__).resolve().parents[3] / "messages" / "pt-BR.json"


def carregar() -> dict:
    with open(_caminho_catalogo(), encoding="utf-8") as fh:
        return json.load(fh)


def t(chave: str, catalogo: dict, **params: object) -> str:
    """Interpola {placeholder} — concatenação de fragmentos é proibida (ADR-0009)."""
    node: object = catalogo
    for parte in chave.split("."):
        if not isinstance(node, dict) or parte not in node:
            return chave  # chave órfã: aparece crua — teste de completude pega
        node = node[parte]
    texto = node if isinstance(node, str) else str(node)
    for nome, valor in params.items():
        texto = texto.replace("{" + nome + "}", str(valor))
    return texto
