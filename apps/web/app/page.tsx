"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8010";

type Msg = { role: "lead" | "agente"; texto: string };
type Quote = {
  plano_nome: string;
  premio_mensal: number;
  franquia: number;
  coberturas: string[];
  carencia: { dias: number };
} | null;
type Handoff = { motivo: string } | null;

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export default function Chat() {
  const [convId, setConvId] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [estado, setEstado] = useState("");
  const [quote, setQuote] = useState<Quote>(null);
  const [handoff, setHandoff] = useState<Handoff>(null);
  const [pensando, setPensando] = useState(false);
  const [entrada, setEntrada] = useState("");
  const fim = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API}/conversations`, { method: "POST" })
      .then((r) => r.json())
      .then((c) => {
        setConvId(c.conversation_id);
        setEstado(c.estado);
      });
  }, []);

  useEffect(() => {
    fim.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, pensando]);

  const enviar = useCallback(
    async (texto: string) => {
      if (!convId || !texto.trim() || pensando) return;
      setMsgs((m) => [...m, { role: "lead", texto }]);
      setEntrada("");
      setPensando(true);
      try {
        const r = await fetch(`${API}/conversations/${convId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: texto }),
        });
        const body = await r.json();
        setEstado(body.estado);
        setQuote(body.cotacao ?? null);
        setHandoff(body.handoff ?? null);
        setMsgs((m) => [...m, { role: "agente", texto: body.reply?.texto ?? "…" }]);
      } catch {
        setMsgs((m) => [...m, { role: "agente", texto: "Conexão falhou — tenta de novo." }]);
      } finally {
        setPensando(false);
      }
    },
    [convId, pensando],
  );

  return (
    <main className="chat-wrap">
      <header className="topo">
        <h1>🚗 AutoSeguro</h1>
        <div className="acoes">
          <Link href="/handoffs" className="link-fila">fila</Link>
          <button
            className="exportar"
            onClick={async () => {
              if (!convId) return;
              const r = await fetch(`${API}/conversations/${convId}/export?fmt=md`);
              const texto = await r.text();
              const url = URL.createObjectURL(new Blob([texto], { type: "text/markdown" }));
              const a = document.createElement("a");
              a.href = url;
              a.download = `conversa-${convId}.md`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            exportar
          </button>
          <span className={`estado ${handoff ? "handoff" : ""}`}>
            {handoff ? `handoff: ${handoff.motivo}` : estado || "…"}
          </span>
        </div>
      </header>

      <section className="msgs">
        {msgs.map((m, i) => (
          <div key={i} className={`bolha ${m.role}`}>
            {m.texto}
          </div>
        ))}
        {pensando && <div className="bolha agente digitando">pensando…</div>}

        {quote && (
          <div className="quote-card">
            <strong>{quote.plano_nome}</strong>
            <div className="premio">{brl(quote.premio_mensal)}/mês</div>
            <div className="linha">franquia {brl(quote.franquia)}</div>
            <div className="linha">{quote.coberturas.join(" · ")}</div>
            <div className="linha carencia">
              carência {quote.carencia.dias} dias (roubo/furto)
            </div>
          </div>
        )}

        {handoff && (
          <div className="handoff-banner">
            👤 Transferido para um vendedor humano — motivo: <b>{handoff.motivo}</b>
          </div>
        )}
        <div ref={fim} />
      </section>

      <form
        className="entrada"
        onSubmit={(e) => {
          e.preventDefault();
          enviar(entrada);
        }}
      >
        <input
          value={entrada}
          onChange={(e) => setEntrada(e.target.value)}
          placeholder={handoff ? "aguardando vendedor…" : "Escreva sua mensagem…"}
          disabled={!!handoff}
        />
        <button type="submit" disabled={!!handoff || pensando}>
          Enviar
        </button>
      </form>
      {convId && <footer className="rodape">sessão: {convId}</footer>}
    </main>
  );
}
