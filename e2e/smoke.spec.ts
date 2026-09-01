import { test, expect } from "@playwright/test";

// Smoke PÓS-DEPLOY (pipeline da demo real — Etapa 16): falha = rollback.
// Roda contra E2E_BASE_URL da demo (Vercel + Railway).
// Alvo: <1 min. Não confundir com E2E do compose (critical-flows).

test("health do agent-api reporta agent e legado", async ({ request }) => {
    const api = process.env.AGENT_API_URL ?? "https://agent-api-demo.up.railway.app";
    const res = await request.get(`${api}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.agent).toBe("ok");
    expect(["ok", "degradado"]).toContain(body.legado);
});

test("home abre e o chat responde 1 turno de verdade", async ({ page }) => {
    test.fixme(); // até a demo existir
    // 1. page.goto("/") → título/tela do chat visíveis (Lighthouse-able)
    // 2. criar conversa + enviar "oi" → resposta do agente chega (p95 < 5s)
    // 3. correlation id presente no rodapé
    expect(true).toBe(true);
});
