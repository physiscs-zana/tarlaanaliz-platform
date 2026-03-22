/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-013: OpenGraph gorsel — sosyal medya paylasimlari icin 1200x630 dinamik gorsel. */

import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "TarlaAnaliz - Drone ile Tarla Analizi";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #059669 0%, #047857 50%, #065f46 100%)",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {/* Logo */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            marginBottom: "32px",
          }}
        >
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "16px",
              background: "#34d399",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "32px",
              color: "white",
              fontWeight: 900,
            }}
          >
            T
          </div>
          <div style={{ fontSize: "48px", fontWeight: 800, color: "white" }}>
            TarlaAnaliz
          </div>
        </div>

        {/* Slogan */}
        <div
          style={{
            fontSize: "36px",
            fontWeight: 700,
            color: "#d1fae5",
            textAlign: "center",
            maxWidth: "900px",
            lineHeight: 1.3,
          }}
        >
          Tarlanizin &quot;check-up ve tahlilini&quot; yaptirin
        </div>
        <div
          style={{
            fontSize: "36px",
            fontWeight: 700,
            color: "white",
            textAlign: "center",
            maxWidth: "900px",
            marginTop: "8px",
          }}
        >
          masrafinizi azaltin!
        </div>

        {/* Alt bilgi */}
        <div
          style={{
            marginTop: "40px",
            display: "flex",
            gap: "32px",
            fontSize: "20px",
            color: "#a7f3d0",
          }}
        >
          <span>Erken Uyari</span>
          <span>|</span>
          <span>Hedefli Ilaclama</span>
          <span>|</span>
          <span>Rapor + Harita</span>
        </div>

        {/* Domain */}
        <div
          style={{
            position: "absolute",
            bottom: "24px",
            fontSize: "18px",
            color: "#6ee7b7",
          }}
        >
          tarlaanaliz.com
        </div>
      </div>
    ),
    { ...size },
  );
}
