"use client";

import type { components } from "@/types/api";

export type Quote = components["schemas"]["QuoteView"];
export type Handoff = components["schemas"]["HandoffView"];
export type TurnoResponse = components["schemas"]["TurnoResponse"];

export const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export function MessageBubble({
  role,
  texto,
}: {
  role: "lead" | "agente";
  texto: string;
}) {
  return <div className={`bolha ${role}`}>{texto}</div>;
}

export function Digitando() {
  return <div className="bolha agente digitando">pensando…</div>;
}

export function QuoteCard({ quote }: { quote: Quote }) {
  return (
    <div className="quote-card" aria-label={`cotação ${quote.plano_nome}`}>
      <strong>{quote.plano_nome}</strong>
      <div className="premio">{brl(quote.premio_mensal)}/mês</div>
      <div className="linha">franquia {brl(quote.franquia)}</div>
      <div className="linha">{quote.coberturas.join(" · ")}</div>
      <div className="linha carencia">
        carência {quote.carencia.dias} dias (roubo/furto)
      </div>
    </div>
  );
}

export function HandoffBanner({ motivo }: { motivo: string }) {
  return (
    <div className="handoff-banner" role="status">
      👤 Transferido para um vendedor humano — motivo: <b>{motivo}</b>
    </div>
  );
}
