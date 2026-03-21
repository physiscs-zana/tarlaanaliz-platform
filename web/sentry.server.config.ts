/*
 * BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
 * PATH: web/sentry.server.config.ts
 * DESC: Sentry error tracking placeholder (server-side).
 *
 * @sentry/nextjs SDK su an yuklu degil. SDK yuklendiginde bu dosya
 * Sentry.init() cagrisi ile degistirilmeli:
 *
 *   pnpm add @sentry/nextjs
 *   // sonra bu dosyayi Sentry docs'a gore guncelleyin.
 *
 * SENTRY_DSN .env'de tanimli.
 * KR-050: sendDefaultPii: false — PII gondermeme.
 */

export {};
