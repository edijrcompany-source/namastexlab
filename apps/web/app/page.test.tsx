import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Chat from "@/app/page";

const API = "http://localhost:8010";

function mockFetchsequence(respostas: {
  criar?: unknown;
  mensagem?: unknown | ((n: number) => unknown);
}) {
  let mensagens = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = { ok: true, text: async () => "markdown da conversa" };
      if (url.endsWith("/conversations"))
        return { ...body, json: async () => respostas.criar } as Response;
      if (url.endsWith("/messages")) {
        mensagens += 1;
        const r =
          typeof respostas.mensagem === "function"
            ? (respostas.mensagem as (n: number) => unknown)(mensagens)
            : respostas.mensagem;
        return { ...body, json: async () => r } as Response;
      }
      throw new Error(`unexpected ${url}`);
    }),
  );
}

beforeEach(() => {
  vi.unstubAllGlobals();
});

it("cria a conversa ao carregar e mostra o estado", async () => {
  mockFetchsequence({ criar: { conversation_id: "01AAA", estado: "QUALIFICANDO" } });
  render(<Chat />);
  await waitFor(() => expect(screen.getByText("QUALIFICANDO")).toBeInTheDocument());
  expect(screen.getByText("sessão: 01AAA")).toBeInTheDocument();
});

it("envia mensagem, recebe reply com cotação e renderiza QuoteCard", async () => {
  const user = userEvent.setup();
  mockFetchsequence({
    criar: { conversation_id: "01BBB", estado: "QUALIFICANDO" },
    mensagem: {
      conversation_id: "01BBB",
      estado: "COTACAO_APRESENTADA",
      reply: { role: "agente", tipo: "text", texto: "Saiu a cotação! Plano Essencial", criado_em: "2026-09-01T12:00:00Z" },
      eventos: [],
      cotacao: {
        quote_id: "01CCC", plano_id: "essencial", plano_nome: "Essencial",
        premio_mensal: 155.87, franquia: 4500,
        coberturas: ["colisao", "roubo", "furto"],
        multiplicadores: { faixa_etaria: 1, idade_veiculo: 1, regiao: 1.3 },
        carencia: { coberturas: ["roubo", "furto"], dias: 30 },
        pro_rata: null, moeda: "BRL", tentativas: 1, duracao_ms: 300,
      },
      handoff: null,
    },
  });
  render(<Chat />);
  const input = await screen.findByLabelText("mensagem");
  await user.type(input, "é isso");
  await user.click(screen.getByRole("button", { name: "Enviar" }));

  await waitFor(() => expect(screen.getByText(/155,87/)).toBeInTheDocument());
  expect(screen.getByText(/carência 30 dias/)).toBeInTheDocument();
  expect(screen.getByText("Saiu a cotação! Plano Essencial")).toBeInTheDocument();
});

it("handoff bloqueia o input e mostra o banner (C1 final)", async () => {
  const user = userEvent.setup();
  mockFetchsequence({
    criar: { conversation_id: "01DDD", estado: "QUALIFICANDO" },
    mensagem: {
      conversation_id: "01DDD",
      estado: "HANDOFF",
      reply: { role: "agente", tipo: "text", texto: "Fechado!", criado_em: "2026-09-01T12:01:00Z" },
      eventos: [],
      cotacao: null,
      handoff: { id: "01EEE", conversation_id: "01DDD", motivo: "aceite_fechamento", resumo: "r", criado_em: "2026-09-01T12:01:00Z", status: "pendente" },
    },
  });
  render(<Chat />);
  const input = await screen.findByLabelText("mensagem");
  await user.type(input, "fechado!");
  await user.click(screen.getByRole("button", { name: "Enviar" }));

  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("aceite_fechamento"));
  expect(input).toBeDisabled();
  expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  expect(input).toHaveAttribute("placeholder", "aguardando vendedor…");
});

it("erro de conexão mostra mensagem amigável", async () => {
  const user = userEvent.setup();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/conversations"))
        return { ok: true, json: async () => ({ conversation_id: "01FFF", estado: "OK" }) } as Response;
      throw new Error("network"); // POST /messages falha
    }),
  );
  render(<Chat />);
  const input = await screen.findByLabelText("mensagem");
  await user.type(input, "oi");
  await user.click(screen.getByRole("button", { name: "Enviar" }));
  await waitFor(() => expect(screen.getByText(/Conexão falhou/)).toBeInTheDocument());
});

it("falha ao criar a conversa avisa o usuário (UX: nunca fica mudo)", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("network");
    }),
  );
  render(<Chat />);
  await waitFor(() => expect(screen.getByText(/SEM_CONEXÃO/)).toBeInTheDocument());
});
