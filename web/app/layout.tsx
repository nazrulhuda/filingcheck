import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SENTENCE } from "@/lib/glance";

import "./globals.css";

// The favicon is app/icon.svg and the link preview app/opengraph-image.tsx (Next.js adds both).
export const metadata: Metadata = {
  metadataBase: new URL("https://filingcheck.vercel.app"),
  title: "FilingCheck",
  description: SENTENCE,
  openGraph: {
    title: "FilingCheck",
    description: SENTENCE,
    url: "/",
    siteName: "FilingCheck",
    type: "website",
  },
  twitter: { card: "summary_large_image", title: "FilingCheck", description: SENTENCE },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
