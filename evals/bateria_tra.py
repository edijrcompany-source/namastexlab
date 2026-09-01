"""Bateria TRA (T-16) — a métrica norte medida (SLO-3, meta ≥70%).

Roda N conversas de leads ELEGÍVEIS com ACL probabilística (p_falha=0.30 por
tentativa — o pior caso do legado) + retry + breaker (clock fake: 60s entre
conversas para o cooldown conviver, como no teste NFR-04).

TRA = conversas que terminaram com COTAÇÃO ENTREGUE sem intervenção humana.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS.parent / "services" / "agent-api"))

import httpx  # noqa: E402

from app.conversation.orchestrator import TurnOrchestrator  # noqa: E402
from app.domain.extraction import Campos  # noqa: E402
from app.llm.fake import FakeLLM  # noqa: E402
from app.quoting.breaker import CircuitBreaker  # noqa: E402
from app.quoting.client import QuoteAcl, QuoteAclConfig  # noqa: E402


class ClockFake:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def acl_do_pior_caso(seed: int, clock: ClockFake) -> QuoteAcl:
    """QuoteAcl REAL (retry 3x + breaker) sobre transporte probabilístico 30%.
    O tempo avança 60s por request: o cooldown do breaker vence entre conversas
    (mesma semântica do teste NFR-04)."""
    rng = random.Random(seed)  # noqa: S311

    def handler(request: httpx.Request) -> httpx.Response:
        clock.now += 60.0
        if rng.random() < 0.30:
            return httpx.Response(503, json={"error": "upstream_unavailable"})
        payload = json.loads(request.content)
        premio = round(119.90 * (1.3 if str(payload.get("cep", "")).startswith("01") else 1.0), 2)
        return httpx.Response(
            200,
            json={
                "plano_id": "essencial",
                "plano_nome": "Essencial",
                "premio_mensal": premio,
                "franquia": 4500.0,
                "coberturas": ["colisao", "roubo", "furto"],
                "carencia": {"coberturas": ["roubo", "furto"], "dias": 30},
                "moeda": "BRL",
            },
        )

    return QuoteAcl(
        base_url="http://legado.test",
        http=httpx.Client(transport=httpx.MockTransport(handler)),
        config=QuoteAclConfig(),
        breaker=CircuitBreaker(clock=clock),
        clock=clock,
        sleeper=lambda _s: None,  # não dormir na bateria
        rng=random.Random(seed),  # noqa: S311
    )


def main(n: int = 200) -> None:
    clock = ClockFake()
    acl = acl_do_pior_caso(seed=42, clock=clock)
    orch = TurnOrchestrator(llm=FakeLLM(), acl=acl, store=None)

    rng = random.Random(7)  # noqa: S311
    resolvidas = 0
    motivos_falha: dict[str, int] = {}

    for i in range(n):
        conv = orch.iniciar()
        idade = rng.randint(25, 70)
        ano = rng.randint(2008, 2024)
        cep = rng.choice(["01310-100", "71010-000"])
        msgs = [
            f"oi, quero cotar o seguro do meu carro",
            f"carro {ano}, tenho {idade} anos, CEP {cep}",
            "é isso",
        ]
        for msg in msgs:
            conv = orch.processar(conv.id, texto=msg)

        if conv.cotacoes:
            resolvidas += 1
        else:
            estado = conv.estado.value if conv.handoff is None else f"handoff:{conv.handoff['motivo']}"
            motivos_falha[estado] = motivos_falha.get(estado, 0) + 1

    tra = 100 * resolvidas / n
    print("═" * 58)
    print(f" Bateria TRA: {resolvidas}/{n} conversas elegíveis resolveram sozinhas")
    print(f" TRA = {tra:.1f}%   (meta SLO-3: ≥ 70%)")
    if motivos_falha:
        print(" não-resolvidas por motivo:")
        for motivo, qtd in sorted(motivos_falha.items()):
            print(f"   {motivo}: {qtd}")
    print("═" * 58)
    if tra < 70.0:
        print("❌ TRA abaixo da meta")
        raise SystemExit(1)
    print("✅ TRA dentro da meta")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
