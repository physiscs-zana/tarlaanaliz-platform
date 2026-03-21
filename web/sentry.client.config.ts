/*
 * BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
 * PATH: web/sentry.client.config.ts
 * DESC: Sentry error tracking configuration (client-side).
 *
 * Bu dosya @sentry/nextjs SDK yuklendikten sonra aktif olur.
 * SDK yuklemek icin: pnpm add @sentry/nextjs
 * Sonra next.config.mjs'de withSentryConfig() wrapper ekleyin.
 *
 * SENTRY_DSN .env'den okunur (NEXT_PUBLIC_SENTRY_DSN olarak expose edilmeli).
 * DSN bos veya tanimsizsa Sentry devre disi kalir — production guvenli.
 */

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN || "";
const TRACES_SAMPLE_RATE = parseFloat(
  process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1",
);

function initSentry(): void {
  // @sentry/nextjs yuklu degilse sessizce cik
  let Sentry: typeof import("@sentry/nextjs") | undefined;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    Sentry = require("@sentry/nextjs");
  } catch {
    return; // SDK yuklu degil — sessizce gec
  }

  if (!SENTRY_DSN) return; // DSN tanimsiz — devre disi

  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: TRACES_SAMPLE_RATE,
    environment: process.env.NODE_ENV || "development",
    // KR-050: PII gondermeme — kullanici bilgisi Sentry'ye akmaz
    sendDefaultPii: false,
    // Production'da replay kapatik — performans onceligi
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.1,
  });
}

initSentry();

export {};
