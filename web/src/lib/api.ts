/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: Backend API base URL resolution for client-side requests. */

/**
 * Returns the backend API base URL (e.g. "https://api.tarlaanaliz.com/api/v1").
 * Falls back to "/api/v1" for relative requests during SSR or when env is missing.
 */
export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "/api/v1";
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
