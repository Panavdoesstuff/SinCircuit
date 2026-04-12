import type { Metadata } from "next";
import { Bebas_Neue, JetBrains_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";

const bebasNeue = Bebas_Neue({ variable: "--font-bebas", weight: "400", subsets: ["latin"] });
const jetBrainsMono = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });
const playfair = Playfair_Display({ variable: "--font-playfair", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BetSmart AI — Intelligent Betting Strategy",
  description:
    "AI-powered betting assistant for sports, casino, poker and more. Get real-time arbitrage, EV analysis, and expert strategy advice.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${bebasNeue.variable} ${jetBrainsMono.variable} ${playfair.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
