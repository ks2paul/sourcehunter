import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SourceHunter",
  description: "Supplier discovery and procurement intelligence",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
