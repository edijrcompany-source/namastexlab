/** Testes para cobrir os gaps de coverage até 99% (layout + export + edges). */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import RootLayout from "@/app/layout";
import Chat from "@/app/page";
import Fila from "@/app/handoffs/page";
import { brl, MessageBubble } from "@/app/components";

// ── layout.tsx (0% → 100%) ────────────────────────────────────────────────
describe("RootLayout", () => {
  it("renderiza html/body com lang pt-BR e children", () => {
    const { container } = render(
      <RootLayout>
        <div data-testid="child">conteúdo</div>
      </RootLayout>,
    );
    expect(container.querySelector("html")).toHaveAttribute("lang", "pt-BR");
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });
});

// ── page.tsx export handler (78% → 99%) ──────────────────────────────────
describe("Chat — export button", () => {
  it("baixa markdown quando clicado (URL.createObjectURL mockado)", async () => {
    const user = userEvent.setup();
    const clickSpy = vi.fn();
    const revokeSpy = vi.fn();

    // mock URL.createObjectURL + revokeObjectURL (jsdom não tem)
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: vi.fn().mockReturnValue("blob:mock"),
      revokeObjectURL: revokeSpy,
    });
    // mock anchor click
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(clickSpy);

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/conversations")) {
          return {
            ok: true,
            json: async () => ({ conversation_id: "01EXPORT", estado: "OK" }),
          } as Response;
        }
        if (url.includes("export")) {
          return {
            ok: true,
            text: async () => "# Conversa exportada\n**Agente**: teste",
          } as Response;
        }
        return { ok: true, json: async () => ({}) } as Response;
      }),
    );

    render(<Chat />);
    const btn = await screen.findByRole("button", { name: "exportar" });
    await user.click(btn);

    await waitFor(() => expect(clickSpy).toHaveBeenCalled());
    expect(revokeSpy).toHaveBeenCalled();

    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("não exporta sem conversation_id", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network"); // criação falha → convId null
      }),
    );
    render(<Chat />);
    const btn = await screen.findByRole("button", { name: "exportar" });
    await user.click(btn); // não deve explodir
    expect(btn).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

// ── handoffs/page.tsx linha 32 (catch do fetch) ───────────────────────────
describe("Fila — erro de rede", () => {
  it("mostra lista vazia quando fetch falha (não crasha)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network");
      }),
    );
    render(<Fila />);
    await waitFor(() => expect(screen.getByText(/fila limpa/i)).toBeInTheDocument());
    vi.unstubAllGlobals();
  });
});

// ── components.tsx edges ──────────────────────────────────────────────────
describe("MessageBubble — edge cases", () => {
  it("renderiza texto vazio sem crashar", () => {
    render(<MessageBubble role="agente" texto="" />);
    expect(document.querySelector(".bolha.agente")).toBeInTheDocument();
  });

  it("renderiza texto com quebras de linha", () => {
    render(<MessageBubble role="lead" texto={"linha 1\nlinha 2"} />);
    expect(document.querySelector(".bolha.lead")).toBeInTheDocument();
  });
});

describe("brl — formatos adicionais", () => {
  it("lida com zero", () => {
    expect(brl(0)).toMatch(/0,00/);
  });
  it("lida com valores altos", () => {
    expect(brl(99999.99)).toMatch(/99\.999,99/);
  });
});
