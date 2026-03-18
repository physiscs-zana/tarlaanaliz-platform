/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: global metadata/trace yapısı genişlemeye açık tutulur. */
/* SEC: Nonce-based CSP — nonce middleware tarafından üretilir, layout'ta uygulanır. */

import type { Metadata } from "next";
import type { ReactNode } from "react";
import { headers } from "next/headers";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "TarlaAnaliz Platform",
  description: "Role-based workflows for admin, expert, farmer and pilot users.",
};

interface RootLayoutProps {
  readonly children: ReactNode;
}

function AppProviders({ children }: RootLayoutProps) {
  // Theme/Auth/Query provider zinciri için genişleme noktası.
  return <>{children}</>;
}

export default function RootLayout({ children }: RootLayoutProps) {
  const nonce = headers().get("x-nonce") ?? "";

  return (
    <html lang="tr">
      <head>
        <meta property="csp-nonce" content={nonce} />
      </head>
      <body nonce={nonce}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
