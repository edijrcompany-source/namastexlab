# ADR-0001 — Front Next.js hospedado na Vercel

**Status:** aceito (01/09/2026) · **Origem:** decisão D1 do usuário

## Contexto
O desafio exige demo pública avaliável: um chat onde o avaliador conversa com o
Agente, vê a timeline rastreável e exporta o log de execução. O front não tem
estado de servidor próprio (todo estado vive no backend — serverless-safe,
spec §8). Time de 1 pessoa, ~3 dias.

## Decisão
**Next.js (App Router) hospedado na Vercel**, região `gru1` (São Paulo),
deploy automático a partir do GitHub. Front é 100% client-side para o chat
(SSR só para meta/SEO eventual).

## Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **Vite + React puro** | Menos camadas, bundle menor | Zero convenção de rota/estrutura; sem preview-deploy maduro fora da Vercel; configuração manual | Descartada — ganho marginal |
| **Remix** | Excelente para forms/SSR | Nosso caso é client-heavy (chat); SSR não agrega | Descartada |
| **Servir UI pelo agent-api (sem front separado)** | 1 container a menos | Perde preview deploys, CDN, responsividade de implantação independente; mistura bordas | Descartada — D1 do usuário |

## Consequências
**Positivas:** preview por PR (avaliar mudanças de UI isoladamente) · CDN/SSL
grátis · co-localização com a região do backend (gru) · ecosystem Next
(Lighthouse alto por padrão, NFR-18).
**Negativas/riscos:** mais um provedor no pipeline (mitigado: front é
stateless, deploy trivial) · limites do plano Hobby (suficiente para demo).
**Reversibilidade:** alta — front é uma casca fina sobre a API do agent-api.
