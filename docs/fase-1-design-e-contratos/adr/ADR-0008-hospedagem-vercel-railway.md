# ADR-0008 — Hospedagem: Vercel (front) + Railway (backend), região GRU

**Status:** aceito (01/09/2026) · **Origem:** decisões D2/D4 do usuário

## Contexto
Demo pública para avaliador no Brasil; dev local via compose (D4). Precisa:
deploy de Dockerfile sem refactor, Postgres gerenciado (ADR-0006), secrets,
região próxima, custo ≤ US$ 10/mês, zero hibernação durante a avaliação.

## Decisão
- **Front:** Vercel (ADR-0001), região `gru1`.
- **Backend:** projeto único no **Railway** com 3 serviços — `agent-api`,
  `quote-api` (build do Dockerfile do desafio, **sem alteração**) e Postgres —
  região **São Paulo**, comunicação interna por rede privada do projeto.
- **CI/CD:** GitHub Actions → GHCR → Railway (backend) e Vercel via integração
  de repo (front). Detalhes na Etapa 13/14.

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Fly.io** | Dockerfile nativo, machines rápidas, `gru` | Multi-container (3 serviços) mais manual que Railway; Postgres separado | Reserva (migração simples se necessário) |
| **Render** | Simples | Free tier **hiberna** — demo fria na hora da avaliação = risco inaceitável | Descartado |
| **Cloud Run** | Scale-to-zero, preço | Setup registry+IAM+multi-serviço; compose não nativo; esforço desproporcional | Descartado |
| **VPS Hetzner + compose** | Custo baixo, controle total | TLS/backup/uptime operados por nós durante o prazo; RTO manual viola NFR-07 facilmente | Descartado para a demo |
| **Railway** ✅ | 3 serviços + DB num projeto, rede privada interna, variáveis/secrets, região SP, deploy por Dockerfile/registry | Custo fixo ~US$5 | **Aceita** |

## Consequências
**Positivas:** dev local (compose) e produção compartilham os mesmos
Dockerfiles; `quote-api` sobe idêntico ao do desafio; segredos fora do repo
(NFR-13).
**Negativas/riscos:** dois provedores (Vercel+Railway) — mitigado: front
stateless, backend autocontido; dependência do SLA de dois manageds para a
disponibilidade NFR-06 (monitor por uptime ping externo).
