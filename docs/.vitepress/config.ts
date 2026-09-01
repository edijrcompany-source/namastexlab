import { defineConfig } from 'vitepress'

// Portal de documentação viva (Etapa 12) — publica no GitHub Pages a cada merge (job docs, Etapa 16).
// Regra: conteúdo gerado é EMBUTIDO pelo build (Redoc/schemas/catálogo); aqui só navegação.
export default defineConfig({
  title: 'AutoSeguro Sales Agent',
  description: 'Documentação viva — desafio FDE Namastex (agente de vendas de seguro auto)',
  lang: 'pt-BR',
  cleanUrls: true,
  themeConfig: {
    nav: [
      { text: '📚 Tutorial', link: '/tutorial' },
      { text: '🔧 How-to', link: '/how-to' },
      { text: '📖 Referência', link: '/referencia' },
      { text: '💡 Explicação', link: '/fase-0-negocio-e-requisitos/etapa-1-modelo-de-negocio' },
      { text: '🚑 Runbooks', link: '/runbooks' },
    ],
    sidebar: {
      '/referencia': [
        {
          text: 'Referência (gerada, nunca à mão)',
          items: [
            { text: 'Visão geral', link: '/referencia' },
            { text: 'API agent-api (Redoc)', link: '/referencia#api-agent-api-redoc' },
            { text: 'API legado — as-consumed', link: '/referencia#api-legado-quote-api-as-consumed' },
            { text: 'Glossário (linguagem ubíqua)', link: '/fase-0-negocio-e-requisitos/etapa-1-linguagem-ubiqua' },
            { text: 'Catálogo de mensagens', link: '/referencia#catálogo-de-mensagens' },
            { text: 'Comandos (make help)', link: '/referencia#comandos' },
          ],
        },
      ],
      '/fase-': [
        {
          text: 'Processo (21 etapas)',
          items: [
            { text: 'Índice e status', link: '/README' },
            { text: 'Fase 0 — Negócio (1-3)', collapsed: true, items: [
              { text: 'Modelo de negócio', link: '/fase-0-negocio-e-requisitos/etapa-1-modelo-de-negocio' },
              { text: 'Linguagem ubíqua', link: '/fase-0-negocio-e-requisitos/etapa-1-linguagem-ubiqua' },
              { text: 'Event storming', link: '/fase-0-negocio-e-requisitos/etapa-1-event-storming' },
              { text: 'Requisitos e NFRs', link: '/fase-0-negocio-e-requisitos/etapa-2-requisitos-e-nfrs' },
              { text: 'PRD', link: '/fase-0-negocio-e-requisitos/etapa-3-prd' },
              { text: '⭐ Spec técnica', link: '/fase-0-negocio-e-requisitos/etapa-3-spec' },
              { text: 'Tasks (T-01..T-17)', link: '/fase-0-negocio-e-requisitos/etapa-3-tasks' },
              { text: 'Template de ticket', link: '/fase-0-negocio-e-requisitos/etapa-3-template-ticket' },
            ]},
            { text: 'Fase 1 — Design (4-10)', collapsed: true, items: [
              { text: 'Arquitetura C4', link: '/fase-1-design-e-contratos/etapa-4-arquitetura-c4' },
              { text: 'ADRs 0001-0011', link: '/fase-1-design-e-contratos/adr/README' },
              { text: 'Contratos API-first', link: '/fase-1-design-e-contratos/etapa-5-contratos' },
              { text: 'Erros e resiliência', link: '/fase-1-design-e-contratos/etapa-6-erros-resiliencia' },
              { text: 'i18n', link: '/fase-1-design-e-contratos/etapa-7-i18n' },
              { text: 'Dados e migrações', link: '/fase-1-design-e-contratos/etapa-8-modelo-de-dados' },
              { text: 'Mensageria', link: '/fase-1-design-e-contratos/etapa-9-mensageria' },
              { text: 'Threat model', link: '/fase-1-design-e-contratos/etapa-10-threat-model' },
            ]},
            { text: 'Fase 2 — Fundação (11-14)', collapsed: true, items: [
              { text: 'Estrutura do repo', link: '/fase-2-fundacao-de-engenharia/etapa-11-estrutura-repo' },
              { text: 'Docs vivas', link: '/fase-2-fundacao-de-engenharia/etapa-12-docs-vivas' },
            ]},
            { text: 'Diagramas as-code', link: '/diagramas-as-code' },
          ],
        },
      ],
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/' },
    ],
  },
})
