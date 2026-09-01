"""build_silver — Bronze → Silver (spec §7 / US-13, T-08).

Regras:
1. Ler Bronze; ordenar por conversation_id, message_index (NUNCA timestamp).
2. Masking §3 itens 1-5 em message_body e sender_name (inicial + ***).
3. veiculo_texto → marca/modelo/ano (dicionário fechado do gerador do desafio).
4. Relatório de saída: nº conversas · % PII mascarada (gate 100%) · % veículo
   normalizado.

Uso:
    uv run --project scripts python scripts/build_silver.py \
        --bronze dataset/conversations.parquet --silver dataset/silver.parquet

A fonte do masking é app.privacy.masking (fonte única — nunca duplicar regex).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "agent-api"))

from app.privacy.masking import mask_for_output  # noqa: E402

# dicionário FECHADO do gerador do desafio (scripts/generate_dataset.py)
MARCAS: dict[str, list[str]] = {
    "Volkswagen": ["Gol", "Polo", "Virtus", "T-Cross", "Nivus"],
    "Chevrolet": ["Onix", "Onix Plus", "Tracker", "Spin"],
    "Fiat": ["Argo", "Mobi", "Cronos", "Pulse", "Toro"],
    "Hyundai": ["HB20", "Creta"],
    "Toyota": ["Corolla", "Yaris", "Corolla Cross"],
    "Honda": ["Civic", "City", "HR-V"],
    "Jeep": ["Renegade", "Compass"],
    "Renault": ["Kwid", "Sandero", "Duster"],
}

_RE_ANO = re.compile(r"\b(19|20)\d{2}\b")

# padrões CRUS para o scan de vazamento do relatório (NFR-12)
_PADRAO_CPF_CRU = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
_PADRAO_EMAIL_CRU = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PADRAO_TELEFONE_CRU = re.compile(r"\+55\s?\d{2}\s?9?\d{4}-?\d{4}")
_PADRAO_PLACA_CRU = re.compile(r"\b[A-Z]{3}-?\d[A-Za-z0-9]\d{2}\b")
_PADRAO_CEP_CRU = re.compile(r"\b\d{5}-\d{3}\b")


def normalizar_veiculo(texto: str | None) -> tuple[str | None, str | None, int | None]:
    """marca/modelo via dicionário fechado; ano por regex (§7.3)."""
    if not texto:
        return None, None, None
    m_ano = _RE_ANO.search(texto)
    ano = int(m_ano.group(0)) if m_ano else None
    for marca, modelos in MARCAS.items():
        if marca.lower() in texto.lower():
            modelo = next((m for m in modelos if m.lower() in texto.lower()), None)
            return marca, modelo, ano
    # marca ausente: modelo ainda pode estar citado ("e um Sandero 2022")
    for marca, modelos in MARCAS.items():
        modelo = next((m for m in modelos if m.lower() in texto.lower()), None)
        if modelo:
            return marca, modelo, ano
    return None, None, ano


def mascarar_linha(body: str, sender: str) -> tuple[str, str]:
    """Masking §3 (saída: inclui CEP) + sender com inicial + ***."""
    body_m = mask_for_output(body)
    sender_m = f"{sender[0]}***" if sender else sender
    return body_m, sender_m


def transformar(bronze: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_parquet(bronze)
    # §7.1 — ordenar por conversation_id, message_index (dataset tem timestamps fora de ordem)
    df = df.sort_values(["conversation_id", "message_index"]).reset_index(drop=True)

    # §7.2 — masking em message_body e sender_name
    df[["message_body", "sender_name"]] = df.apply(
        lambda r: pd.Series(mascarar_linha(str(r.message_body), str(r.sender_name))), axis=1
    )

    # §7.3 — normalização de veículo (colunas novas; texto original preservado)
    veic = df["veiculo_texto"].astype(str).apply(normalizar_veiculo)
    df["marca"] = [v[0] for v in veic]
    df["modelo"] = [v[1] for v in veic]
    df["ano"] = [v[2] for v in veic]

    # §7.5 — relatório com gate: 100% mascarada
    todo_texto = " ".join(df.message_body.astype(str)) + " " + " ".join(df.sender_name.astype(str))
    padroes = (_PADRAO_CPF_CRU, _PADRAO_EMAIL_CRU, _PADRAO_TELEFONE_CRU, _PADRAO_PLACA_CRU, _PADRAO_CEP_CRU)
    vazamentos = sum(len(p.findall(todo_texto)) for p in padroes)
    total_textos = len(df) * 2  # body + sender
    pct_mascarada = round(100 * (1 - min(vazamentos / max(total_textos, 1), 1)), 4)

    relatorio = {
        "mensagens": len(df),
        "conversas": int(df.conversation_id.nunique()),
        "vazamentos_pii": vazamentos,
        "pct_pii_mascarada": pct_mascarada,
        "pct_veiculo_normalizado": round(
            100 * df.marca.notna().sum() / max(len(df), 1), 2
        ),
    }
    return df, relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description="Bronze → Silver (spec §7)")
    parser.add_argument("--bronze", default="dataset/conversations.parquet")
    parser.add_argument("--silver", default="dataset/silver/conversations.parquet")
    args = parser.parse_args()

    silver_path = Path(args.silver)
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    df, relatorio = transformar(Path(args.bronze))
    df.to_parquet(silver_path, index=False)

    print(f"OK: {relatorio['mensagens']} mensagens em {relatorio['conversas']} conversas → {silver_path}")
    print(f"PII mascarada: {relatorio['pct_pii_mascarada']}% (vazamentos: {relatorio['vazamentos_pii']})")
    print(f"Veículo normalizado: {relatorio['pct_veiculo_normalizado']}%")
    if relatorio["pct_pii_mascarada"] != 100.0:
        print("ERRO: Silver com PII crua — NFR-12 violado", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
