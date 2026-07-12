import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Validador Inteligente de Faturas",
  description:
    "Sistema com OCR e inteligência artificial para comparar comprovantes com lançamentos de faturas de cartão.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}