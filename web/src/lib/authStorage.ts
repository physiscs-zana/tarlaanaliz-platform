/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Auth artefact lifecycle (TTL + temizleme) kontrollü tutulur. */
/* SEC-FIX: JWT token artık localStorage'da saklanmıyor (XSS riski).
   Token yalnızca HttpOnly cookie ile taşınır. Bu dosya artık yalnızca
   client-side state (pin artifact) için kullanılır. */

const PIN_KEY = "ta_auth_pin";

interface StoredSecret {
  readonly value: string;
  readonly expiresAt: number;
}

const memoryStore = new Map<string, string>();

// In-memory token cache (never persisted to localStorage)
let _memoryToken: { value: string; expiresAt: number } | null = null;

function getStorage(): Pick<Storage, "getItem" | "setItem" | "removeItem"> {
  if (typeof window !== "undefined" && window.localStorage) {
    return window.localStorage;
  }

  return {
    getItem: (key) => memoryStore.get(key) ?? null,
    setItem: (key, value) => {
      memoryStore.set(key, value);
    },
    removeItem: (key) => {
      memoryStore.delete(key);
    },
  };
}

/**
 * SEC-FIX: Token is stored in memory only (for current-session API calls).
 * The authoritative token is in the HttpOnly cookie set by the server.
 * This in-memory copy is a convenience for client-side Bearer header usage
 * until the API is migrated to read from cookies directly.
 */
export function setAuthToken(token: string, ttlMs: number): void {
  _memoryToken = { value: token, expiresAt: Date.now() + Math.max(0, ttlMs) };
}

export function getAuthToken(): string | null {
  if (!_memoryToken) return null;
  if (_memoryToken.expiresAt <= Date.now()) {
    _memoryToken = null;
    return null;
  }
  return _memoryToken.value;
}

export function setPinArtifact(pinArtifact: string, ttlMs: number): void {
  const expiresAt = Date.now() + Math.max(0, ttlMs);
  const payload: StoredSecret = { value: pinArtifact, expiresAt };
  getStorage().setItem(PIN_KEY, JSON.stringify(payload));
}

export function getPinArtifact(): string | null {
  const raw = getStorage().getItem(PIN_KEY);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as StoredSecret;
    if (payload.expiresAt <= Date.now()) {
      getStorage().removeItem(PIN_KEY);
      return null;
    }
    return payload.value;
  } catch {
    getStorage().removeItem(PIN_KEY);
    return null;
  }
}

export function clearAuthStorage(): void {
  _memoryToken = null;
  getStorage().removeItem(PIN_KEY);
}
