import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "STAT-Learn",
  description:
    "STAT-Learn — AI-Powered Competency & Learning Intelligence Platform for India's Official Statistical System.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body className="font-sans antialiased bg-background text-foreground">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
