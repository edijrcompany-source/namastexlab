import { render, screen } from "@testing-library/react";

import {
  HandoffBanner,
  MessageBubble,
  QuoteCard,
  brl,
  type Quote,
} from "@/app/components";

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

describe("MessageBubble", () => {
  it("renderiza o texto com o papel correto", () => {
    render(<MessageBubble role="lead" texto="oi, quero cotar" />);
    expect(screen.getByText("oi, quero cotar")).toHaveClass("lead");
  });
});

describe("QuoteCard (spec §6.4 — elementos obrigatórios)", () => {
  it("exibe prêmio, franquia, coberturas e carência", () => {
    render(<QuoteCard quote={quote} />);
    expect(screen.getByText(/155,87/)).toBeInTheDocument();
    expect(screen.getByText(/4\.500,00/)).toBeInTheDocument();
    expect(screen.getByText(/colisao · roubo · furto/)).toBeInTheDocument();
    expect(screen.getByText(/carência 30 dias/)).toBeInTheDocument();
  });
});

describe("HandoffBanner", () => {
  it("mostra o motivo do handoff", () => {
    render(<HandoffBanner motivo="aceite_fechamento" />);
    expect(screen.getByRole("status")).toHaveTextContent("aceite_fechamento");
  });
});

describe("brl", () => {
  it("formata pt-BR (etapa-7 §3 — util único)", () => {
    expect(brl(155.87)).toMatch(/155,87/);
    expect(brl(4500)).toMatch(/4\.500,00/);
  });
});
