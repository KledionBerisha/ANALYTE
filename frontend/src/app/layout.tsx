import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AuthProvider } from "@/lib/auth";

import "./globals.css";

// `latin-ext` sjell ë dhe ç; pa të shkronjat shqipe do të vizatoheshin me
// shkronjën rezervë të sistemit, në mes të fjalës.
const inter = Inter({ variable: "--font-inter", subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "ANALYTE — shpjegimi i analizave",
  description: "Shpjegim i verifikuar i analizave laboratorike në shqip.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="sq" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
