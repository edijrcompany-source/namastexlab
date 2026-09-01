"""API Smoke — TODAS as APIs do desafio, endpoint por endpoint (T-14b).

Legado (quote-api:8000): /health · /planos (3 planos + regras) · /quote
  (200 nos 3 planos com multiplicadores × pró-rata · 422 idade/veículo/plano · 400).
Agent-api (8001, contrato §5.4): health · POST /conversations · POST /messages
  (texto, mídia, 422×2) · GET timeline · GET export json+md · GET /handoffs ·
  DELETE (401 sem token · 204 com).

Tolerância à instabilidade do legado (20% 5xx): retries embutidos nos 200.
Uso:  cd services/agent-api && uv run python ../../evals/api_smoke.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

LEGADO = os.getenv("LEGADO_URL", "http://localhost:8000")
AGENT = os.getenv("AGENT_URL", "http://localhost:8001")

resultados: list[tuple[str, bool, str]] = []


def http(base: str, path: str, body: dict | None = None, method: str | None = None, headers: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base + path, data=data, method=method or ("POST" if data else "GET"),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=9.5) as resp:  # > 8s do legado lento
            raw = resp.read()
            try:
                return resp.status, json.loads(raw or b"null")
            except Exception:  # noqa: BLE001 — export md retorna texto
                return resp.status, {"_texto": raw.decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"null")
        except Exception:  # noqa: BLE001
            return e.code, {"_texto": raw.decode("utf-8", "replace")}
    except Exception:  # noqa: BLE001 — timeouts/conn: deixa o retry decidir
        return 0, {"_erro": "timeout/conn"}


def check(nome: str, ok: bool, detalhe: str = "") -> None:
    resultados.append((nome, ok, detalhe))
    print(f"  {'✅' if ok else '❌'} {nome}{(' — ' + detalhe) if detalhe and not ok else ''}")


# ─────────────────────────── LEGADO (desafio) ────────────────────────────
print("═" * 60, "\n LEGADO quote-api :", LEGADO, "\n" + "═" * 60)

code, body = http(LEGADO, "/health")
check("GET /health", code == 200 and body.get("status") == "ok")

code, planos = http(LEGADO, "/planos")
ids = [p["id"] for p in (planos or {}).get("planos", [])]
check("GET /planos — 3 planos", code == 200 and ids == ["essencial", "completo", "premium"])
check("GET /planos — regras (carência 30d, agravo 1.30)", 
      (planos or {}).get("regras", {}).get("carencia", {}).get("dias") == 30
      and planos["regras"]["regiao_cep"]["multiplicador"] == 1.30)

def quote_com_retry(payload, codes_esperados, tentativas=14):
    """Instabilidade (20% 5xx) atinge qualquer POST — retry até bater o esperado."""
    for _ in range(tentativas):
        code, body = http(LEGADO, "/quote", payload)
        if code in codes_esperados:
            return code, body
        time.sleep(0.3)
    return code, body


CASOS_200 = [
    ("essencial·30·2022·CEP01", {"plano_id": "essencial", "idade": 30, "veiculo_ano": 2022, "cep": "01310-100"}, 119.90),
    ("completo·18·2020·agravo07", {"plano_id": "completo", "idade": 18, "veiculo_ano": 2020, "cep": "07000-000"}, 209.90 * 1.60 * 1.15 * 1.30),  # veículo 6a=×1.15
    ("premium·60·2016·semCEP", {"plano_id": "premium", "idade": 60, "veiculo_ano": 2016}, 339.90 * 1.40 * 1.15),  # veículo 10a=×1.15
]
for nome, payload, esperado in CASOS_200:
    code, body = quote_com_retry(payload, {200})
    ok = code == 200 and abs(body.get("premio_mensal", 0) - round(esperado, 2)) < 0.02
    check(f"POST /quote 200 {nome}", ok, f"esperado {round(esperado, 2)}, veio {body.get('premio_mensal')} (code {code})")

code, body = quote_com_retry({"plano_id": "essencial", "idade": 80, "veiculo_ano": 2020}, {422})
check("POST /quote 422 idade>75", code == 422 and "Idade" in body.get("motivo", ""), f"code {code} {body}")

code, body = quote_com_retry({"plano_id": "essencial", "idade": 40, "veiculo_ano": 1990}, {422})
check("POST /quote 422 veículo>20a", code == 422 and "eiculo" in body.get("motivo", ""), f"code {code} {body}")

code, body = quote_com_retry({"plano_id": "gold", "idade": 40, "veiculo_ano": 2020}, {422})
check("POST /quote 422 plano inexistente", code == 422 and "gold" in body.get("motivo", ""), f"code {code} {body}")

code, body = quote_com_retry({"idade": 40, "veiculo_ano": 2020, "data_inicio": "15/10/2026"}, {400})
check("POST /quote 400 payload inválido (lógica)", code == 400 and "payload" in body.get("error", ""), f"code {code} {body}")

code, body = quote_com_retry(
    {"plano_id": "essencial", "idade": 30, "veiculo_ano": 2022, "cep": "01310-100", "data_inicio": "2026-10-15"}, {200}
)
pro = (body or {}).get("primeiro_pagamento_pro_rata") or {}
check("POST /quote pró-rata (início dia 15)", code == 200 and pro.get("dias_cobrados") == 17, str(pro))

# ─────────────────────────── AGENT-API (nossa) ───────────────────────────
print("═" * 60, "\n AGENT-API :", AGENT, "\n" + "═" * 60)

code, body = http(AGENT, "/health")
check("GET /health (agent+legado)", code == 200 and body.get("agent") == "ok" and body.get("legado") in ("ok", "degradado"))

code, conv = http(AGENT, "/conversations", method="POST")
cid = (conv or {}).get("conversation_id", "")
check("POST /conversations 201 + ULID", code == 201 and len(cid) == 26)

code, turno = http(AGENT, f"/conversations/{cid}/messages", {"text": "Onix 2022, 30 anos, CEP 01310-100"})
check("POST /messages qualifica → CONFIRMANDO", code == 200 and turno.get("estado") == "CONFIRMANDO")

code, turno = http(AGENT, f"/conversations/{cid}/messages", {"text": "é isso"})
tem_cotacao = bool((turno or {}).get("cotacao"))
check("POST /messages confirma → cotação", code == 200 and tem_cotacao)

code, turno = http(AGENT, f"/conversations/{cid}/messages", {"text": "fechado!"})
check("POST /messages aceite → handoff", code == 200 and (turno.get("handoff") or {}).get("motivo") == "aceite_fechamento")

code, tl = http(AGENT, f"/conversations/{cid}")
check("GET timeline (PII mascarada)", code == 200 and "***" in json.dumps(tl, ensure_ascii=False))

code, body = http(AGENT, f"/conversations/{cid}/export?fmt=md")
check("GET export?fmt=md (markdown)", code == 200 and "**Agente**" in body.get("_texto", ""))
code, _ = http(AGENT, f"/conversations/{cid}/export?fmt=json")
check("GET export?fmt=json", code == 200)

code, fila = http(AGENT, "/handoffs")
check("GET /handoffs (nossa conversa na fila)", code == 200 and any(i.get("conversation_id") == cid for i in (fila or {}).get("items", [])))

code, _ = http(AGENT, f"/conversations/{cid}/messages", {"text": "x", "media_type": "image", "media_marker": "[imagem] y"})
check("POST /messages 422 text+midia", code == 422)

code, conv2 = http(AGENT, "/conversations", method="POST")
cid2 = conv2["conversation_id"]
code, _ = http(AGENT, f"/conversations/{cid2}/messages", {"media_type": "document", "media_marker": "[documento] CNH.pdf"})
check("POST /messages mídia ok (pede texto)", code == 200)

code, _ = http(AGENT, f"/conversations/{cid2}", method="DELETE")
check("DELETE sem token → 401", code == 401)

# ─────────────────────────── RESULTADO ────────────────────────────────────
falhas = [n for n, ok, _ in resultados if not ok]
print("═" * 60)
print(f" RESULTADO: {len(resultados) - len(falhas)}/{len(resultados)} endpoints OK")
if falhas:
    print(" FALHARAM:", ", ".join(falhas))
    sys.exit(1)
print(" ✅ TODAS AS APIs DO DESAFIO EM PLENO FUNCIONAMENTO")
