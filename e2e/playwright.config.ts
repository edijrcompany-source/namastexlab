import { defineConfig, devices } from "@playwright/test";

// E2E do produto inteiro contra o COMPOSE completo (Etapa 14 §4).
// Determinismo: o compose de e2e sobe com QUOTE_SEED=42 — as falhas do legado
// tornam-se reproduzíveis (cenários C4/C5 estáveis).
const CI = !!process.env.CI;

export default defineConfig({
    testDir: ".",
    timeout: 60_000,
    retries: CI ? 1 : 0,
    workers: CI ? 1 : undefined, // serializado no CI: uma conversa por vez
    reporter: CI ? [["github"], ["html", { open: "never" }]] : "list",
    use: {
        baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
        trace: "on-first-retry",
        screenshot: "only-on-failure",
    },
    projects: [
        { name: "chromium", use: { ...devices["Desktop Chrome"] } },
        // mobile-first é requisito (NFR-18) — 360px
        { name: "mobile-chrome", use: { ...devices["Pixel 5"] }, testMatch: /critical/ },
    ],
});
