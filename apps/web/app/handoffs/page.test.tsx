import { render, screen, waitFor } from "@testing-library/react";

import Fila from "@/app/handoffs/page";

beforeEach(() => vi.unstubAllGlobals());

it("lista handoffs pendentes com motivo legível", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      ({
        ok: true,
        json: async () => ({
          items: [
            {
              id: "01J8ZBQ4T7X9M2K6P8R0V3WYAC",
              conversation_id: "01J8Z9C3K5M7P9R2T4V6W8YBAA",
              motivo: "aceite_fechamento",
              resumo: "Onix 2022, 30 anos, CEP 01***-***",
              criado_em: "2026-09-01T12:04:01Z",
              status: "pendente",
            },
          ],
        }),
      }) as Response,
    ),
  );
  render(<Fila />);
  await waitFor(() => expect(screen.getByText(/aceite — fechar venda/)).toBeInTheDocument());
  expect(screen.getByText(/Onix 2022/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /abrir conversa/ })).toBeInTheDocument();
});

it("fila vazia mostra estado de vazio (não é erro)", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, json: async () => ({ items: [] }) }) as Response),
  );
  render(<Fila />);
  await waitFor(() => expect(screen.getByText(/fila limpa ✨/)).toBeInTheDocument());
});
