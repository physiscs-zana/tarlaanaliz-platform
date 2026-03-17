// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: Auth artefact lifecycle — authStorage.ts kanonik kaynaktır.
'use client';

import { useCallback, useState } from 'react';

import { setAuthToken, getAuthToken, clearAuthStorage } from '@/lib/authStorage';
import { AUTH_TOKEN_TTL_MS, COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from '@/lib/constants';
import { getApiBaseUrl, decodeJwtPayload } from '@/lib/api';

/**
 * KR-063: SSOT kanonik rol kodları.
 * Middleware ve layout guard'ları ROLE_GROUP üzerinden çalışır;
 * detaylı yetki ayrımı (ör. COOP_OWNER vs COOP_VIEWER) bileşen düzeyinde kontrol edilir.
 */
export type AuthRole =
  | 'FARMER_SINGLE'
  | 'FARMER_MEMBER'
  | 'COOP_OWNER'
  | 'COOP_ADMIN'
  | 'COOP_AGRONOMIST'
  | 'COOP_VIEWER'
  | 'PILOT'
  | 'STATION_OPERATOR'
  | 'IL_OPERATOR'
  | 'CENTRAL_ADMIN'
  | 'BILLING_ADMIN'
  | 'AI_SERVICE'
  | 'EXPERT';

/** Middleware ve layout guard'ları bu grupları kullanır. */
export type RoleGroup = 'farmer' | 'expert' | 'pilot' | 'admin';

/** KR-063: Rol → grup eşlemesi. Middleware ROLE_PREFIXES bu grubu kullanır. */
export const ROLE_TO_GROUP: Record<AuthRole, RoleGroup> = {
  FARMER_SINGLE: 'farmer',
  FARMER_MEMBER: 'farmer',
  COOP_OWNER: 'farmer',
  COOP_ADMIN: 'farmer',
  COOP_AGRONOMIST: 'farmer',
  COOP_VIEWER: 'farmer',
  PILOT: 'pilot',
  STATION_OPERATOR: 'admin',
  IL_OPERATOR: 'admin',
  CENTRAL_ADMIN: 'admin',
  BILLING_ADMIN: 'admin',
  AI_SERVICE: 'admin',
  EXPERT: 'expert',
};

export interface AuthUser {
  id: string;
  role: AuthRole;
  phoneMasked?: string;
}

export interface LoginInput {
  phone: string;
  pin: string;
}

export interface LoginResponse {
  readonly access_token: string;
  readonly user: AuthUser;
}

export interface AuthState {
  token: string | null;
  user: AuthUser | null;
}

/**
 * SEC-FIX: Token cookie is now Secure + SameSite=Strict.
 * TODO: HttpOnly cannot be set from client-side JS. Token cookies should be
 * migrated to server-set Set-Cookie headers (backend login endpoint) so that
 * HttpOnly can be applied and the token is inaccessible to scripts.
 */
function setCookie(name: string, value: string, maxAgeSec: number): void {
  if (typeof document !== 'undefined') {
    document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=${maxAgeSec};Secure;SameSite=Strict`;
  }
}

function clearCookie(name: string): void {
  if (typeof document !== 'undefined') {
    document.cookie = `${name}=;path=/;max-age=0`;
  }
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    token: getAuthToken(),
    user: null,
  });

  const login = useCallback(async (input: LoginInput) => {
    const baseUrl = getApiBaseUrl();
    const response = await fetch(`${baseUrl}/auth/phone-pin/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ phone: input.phone, pin: input.pin }),
    });

    if (response.status === 429) {
      throw new Error('429: Rate limit exceeded');
    }
    if (!response.ok) {
      throw new Error('Login failed');
    }

    const raw = (await response.json()) as {
      access_token: string;
      subject: string;
      phone_verified: boolean;
    };

    // Extract role from JWT claims (backend encodes roles[] in the token)
    const claims = decodeJwtPayload(raw.access_token);
    const roles = (claims.roles as string[] | undefined) ?? [];
    const primaryRole = (roles[0] ?? 'FARMER_SINGLE') as AuthRole;

    const user: AuthUser = {
      id: raw.subject,
      role: primaryRole,
    };
    const data: LoginResponse = { access_token: raw.access_token, user };

    setAuthToken(data.access_token, AUTH_TOKEN_TTL_MS);

    const maxAgeSec = Math.floor(AUTH_TOKEN_TTL_MS / 1000);
    setCookie(COOKIE_TOKEN_KEY, data.access_token, maxAgeSec);
    const roleGroup = ROLE_TO_GROUP[primaryRole] ?? 'farmer';
    setCookie(COOKIE_ROLE_KEY, roleGroup, maxAgeSec);

    setState({ token: data.access_token, user });
    return data;
  }, []);

  const logout = useCallback(() => {
    clearAuthStorage();
    clearCookie(COOKIE_TOKEN_KEY);
    clearCookie(COOKIE_ROLE_KEY);
    setState({ token: null, user: null });
  }, []);

  const isAuthenticated = Boolean(state.token);

  return {
    ...state,
    isAuthenticated,
    login,
    logout,
  };
}
