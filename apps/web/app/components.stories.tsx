/** Stories do chat (Etapa 14 §4 — catálogo vivo).
 *
 * Nota técnica: SB10 (rolldown-vite) tem um parse bug com JSX inline em
 * `render:` — por isso createElement aqui (semântica idêntica, zero JSX).
 */
import { createElement as h } from "react";
import type { Meta, StoryObj } from "@storybook/react-vite";

import {
  HandoffBanner,
  MessageBubble,
  QuoteCard,
  type Quote,
} from "./components";

const quote: Quote = {
  quote_id: "01J8Z9C3K5M7P9R2T4V6W8YBAA",
  plano_id: "essencial",
  plano_nome: "Essencial",
  premio_mensal: 155.87,
  franquia: 4500,
  coberturas: ["colisao", "roubo", "furto"],
  multiplicadores: { faixa_etaria: 1, idade_veiculo: 1, regiao: 1.3 },
  carencia: { coberturas: ["roubo", "furto"], dias: 30 },
  pro_rata: null,
  moeda: "BRL",
  tentativas: 1,
  duracao_ms: 412,
};

export default { title: "Chat", parameters: { layout: "padded" } } satisfies Meta;

export const BolhaLead: StoryObj = {
  render: () => h(MessageBubble, { role: "lead", texto: "Onix 2022, tenho 30 anos" }),
};
export const BolhaAgente: StoryObj = {
  render: () => h(MessageBubble, { role: "agente", texto: "Confirmando: veículo Onix 2022…" }),
};
export const Cotacao: StoryObj = {
  render: () => h(QuoteCard, { quote }),
};
export const Handoff: StoryObj = {
  render: () => h(HandoffBanner, { motivo: "aceite_fechamento" }),
};
