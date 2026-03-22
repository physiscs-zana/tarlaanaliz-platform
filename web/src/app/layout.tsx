/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: global metadata/trace yapısı genişlemeye açık tutulur. */
/* SEC: Nonce-based CSP — nonce middleware tarafından üretilir, layout'ta uygulanır. */

import type { Metadata } from "next";
import type { ReactNode } from "react";
import { headers } from "next/headers";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: {
    default: "TarlaAnaliz - Drone ile Tarla Analizi | Hastalik, Zararli, Ot Tespiti",
    template: "%s | TarlaAnaliz",
  },
  description:
    "TarlaAnaliz drone ile tarla analizi yapar. Hastalik, zararli bocek, yabanci ot ve su eksikligini insan gozunden en az bir hafta once tespit eder. GAP Bolgesi ve tum Turkiye.",
  keywords: [
    "tarla analizi",
    "drone tarla tarama",
    "bitki hastaligi tespit",
    "zararli bocek tespiti",
    "yabanci ot tespiti",
    "tarimsal drone",
    "akilli tarim",
    "hassas tarim",
    "NDVI analizi",
    "tarla saglik haritasi",
    "GAP bolgesi tarim",
    "pamuk hastaligi",
    "bugday analizi",
  ],
  openGraph: {
    title: "TarlaAnaliz - Drone ile Tarla Analizi",
    description:
      "Tarlanizin check-up ve tahlilini drone ile yapiyoruz. Hastalik, zararli bocek, yabanci ot ve su eksikligini erken tespit.",
    url: "https://tarlaanaliz.com",
    siteName: "TarlaAnaliz",
    locale: "tr_TR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "TarlaAnaliz - Drone ile Tarla Analizi",
    description:
      "Tarlanizin check-up ve tahlilini drone ile yapiyoruz. Hastalik, zararli bocek, yabanci ot ve su eksikligini erken tespit.",
  },
  robots: {
    index: true,
    follow: true,
  },
  metadataBase: new URL("https://tarlaanaliz.com"),
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
