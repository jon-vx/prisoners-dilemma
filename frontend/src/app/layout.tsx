import type { Metadata } from "next";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prisoner’s Dilemma",
  description: "Run and compare iterated Prisoner’s Dilemma tournaments.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" className="dark" suppressHydrationWarning>
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <header className="app-header">
          <Link href="/">Prisoner’s Dilemma</Link>
          <span>Tournaments</span>
          <ThemeToggle />
        </header>
        {children}
      </body>
    </html>
  );
}
