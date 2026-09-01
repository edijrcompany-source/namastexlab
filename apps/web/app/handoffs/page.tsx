"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://localhost:8010";

type Item = {
  id: string;
  conversation_id: string;
  motivo: string;
  resumo: string;
  criado_em: string;
  status: string;
};

const MOTIVOS: Record<string, string> = {
  aceite_fechamento: "🎉 aceite — fechar venda",
  inelegivel_contestado: "⚖️ recusa contestada",
  objecao_preco: "💰 objeção de preço",
  preferencia_humana: "👤 pediu humano",
  falha_tecnica: "🔧 sistema instável",
  fora_escopo: "🧭 fora de escopo",
};

export default function Fila() {
  const [itens, setItens] = useState<Item[] | null>(null);

  useEffect(() => {
    fetch(`${API}/handoffs`)
      .then((r) => r.json())
      .then((d) => setItens(d.items))
      .catch(() => setItens([]));
  }, []);

  return (
    <main className="fila-wrap">
      <header className="fila-topo">
        <a href="/" className="voltar">← chat</a>
        <h1>Fila de handoffs</h1>
      </header>

      {itens === null && <p className="vazia">carregando…</p>}
      {itens !== null && itens.length === 0 && (
        <p className="vazia">Nenhuma conversa aguardando — fila limpa ✨</p>
      )}

      {itens?.map((i) => (
        <article key={i.id} className="card">
          <div className="card-topo">
            <strong>{MOTIVOS[i.motivo] ?? i.motivo}</strong>
            <span className="status">{i.status}</span>
          </div>
          <p className="resumo">{i.resumo}</p>
          <div className="card-rodape">
            <span>{new Date(i.criado_em).toLocaleString("pt-BR")}</span>
            <a href={`${API}/conversations/${i.conversation_id}/export?fmt=md`} target="_blank">
              abrir conversa ↗
            </a>
          </div>
        </article>
      ))}
    </main>
  );
}
