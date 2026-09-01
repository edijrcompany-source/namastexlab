import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoSeguro — Agente de vendas",
  description: "Desafio FDE Namastex — converse, qualifique e cote com resiliência",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
