/*
 * BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
 * PATH: web/sentry.client.config.ts
 * DESC: Sentry error tracking placeholder (client-side).
 *
 * @sentry/nextjs SDK su an yuklu degil. SDK yuklendiginde bu dosya
 * Sentry.init() cagrisi ile degistirilmeli:
 *
 *   pnpm add @sentry/nextjs
 *   // sonra bu dosyayi Sentry docs'a gore guncelleyin.
 *
 * SENTRY_DSN .env'de tanimli (NEXT_PUBLIC_SENTRY_DSN).
 * KR-050: sendDefaultPii: false — PII gondermeme.
 */

export {};
