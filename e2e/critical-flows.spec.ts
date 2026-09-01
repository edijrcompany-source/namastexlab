import { test, expect } from "@playwright/test";

// Fluxos críticos C1-C6 (spec §11) — a jornada completa contra o compose
// (agent-api + quote-api com QUOTE_SEED=42 + postgres + front).
// Rodam no CI noturno e PRÉ-RELEASE (portão da Etapa 14) — nunca no PR comum.
//
// Convenção de dados: idades/anos/anos escolhidos para determinismo:
//   C1 feliz:    30 anos, Onix 2022, CEP 01310-100 (agravo região ×1.30)
//   C3/C4:       77 anos (recusa idade — sem chamar o legado)
//   C5:          controlado pelo QUOTE_SEED (falha persistente programada)
//
// NOTE: specs marcados fixme até o front existir (T-11) — a jornada e os
// asserts já são o contrato do teste (TDD: spec → teste → implementação).

test.beforeEach(async ({ page }) => {
    await page.goto("/");
});

test("C1 — caminho feliz até handoff de fechamento", async ({ page }) => {
    test.fixme(); // até T-11
    // 1. enviar "oi, quero cotar um seguro"
    // 2. qualificar: "Onix 2022, tenho 30 anos, CEP 01310-100"
    // 3. confirmar eco
    // 4. aguardar cotação: QuoteCard com prêmio = 119.90*1.0*1.0*1.30 = 155.87
    //    (assert byte a byte — NFR-09), franquia R$ 4.500, carência 30d
    // 5. "fechado!" → HandoffBanner motivo aceite_fechamento
    // 6. export da conversa contém quote_id e eventos com status
});

test("C2 — objeção de preço (2x) escala para humano", async ({ page }) => {
    test.fixme();
    // após cotação: "tá caro" → comparativo de planos (sem desconto)
    // segunda objeção → handoff objecao_preco
});

test("C3 — recusa de inelegibilidade aceita", async ({ page }) => {
    test.fixme();
    // 77 anos → recusa clara SEM chamada ao legado (timeline sem quote_requested)
    // "ok, obrigado" → conversa encerrada perdido_ineligivel
});

test("C4 — recusa contestada vira handoff", async ({ page }) => {
    test.fixme();
    // 77 anos → "tenho certeza? conheço gente que conseguiu" → handoff inelegivel_contestado
});

test("C5 — falha persistente do legado sem preço inventado", async ({ page }) => {
    test.fixme();
    // QUOTE_SEED=42 programa a sequência de falhas: 3 tentativas + circuito
    // resposta honesta SEM qualquer "R$" no texto do agente
    // retentativa agendada; 2ª abertura → handoff falha_tecnica
});

test("C6 — pedido de humano é imediato", async ({ page }) => {
    test.fixme();
    // 2º turno: "quero falar com uma pessoa" → HandoffBanner imediato,
    // sem tentativa de convencer
});

test("visual — QuoteCard e chat @mobile", async ({ page }) => {
    test.fixme();
    // toHaveScreenshot: QuoteCard (prêmio/franquia/carência/pró-rata)
    // e chat em 360px — inclui cenário pseudo-locale (Etapa 7 §6)
});
