/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: Backend API base URL resolution for client-side requests. */

/**
 * Returns the backend API base URL (e.g. "https://api.tarlaanaliz.com/api/v1").
 *
 * Uses NEXT_PUBLIC_API_BASE_URL (defined in .env.example and env.ts PublicEnv)
 * which contains the domain only (e.g. "https://api.tarlaanaliz.com").
 * Falls back to "/api/v1" for relative requests (proxied via next.config.mjs rewrite).
 *
 * ROOT CAUSE FIX: Previously read non-existent NEXT_PUBLIC_API_URL env var,
 * always falling back to "/api/v1" which caused "Failed to fetch" in production
 * when no Next.js rewrite was configured.
 */
export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (base) return `${base.replace(/\/+$/, "")}/api/v1`;
  return "/api/v1";
}

/**
 * Read auth token from cookie (survives page refresh, unlike in-memory store).
 */
export function getTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)ta_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Decode a JWT payload without verification (client-side claim extraction only).
 * The backend is the authority — this is just for reading claims like roles/user_id.
 */
export function decodeJwtPayload(token: string): Record<string, unknown> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return {};
    const payload = parts[1];
    const padded = payload + "=".repeat((4 - (payload.length % 4)) % 4);
    const decoded = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return {};
  }
}
