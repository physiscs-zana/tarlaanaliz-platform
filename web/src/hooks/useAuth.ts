// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: Auth artefact lifecycle — authStorage.ts kanonik kaynaktır.
'use client';

import { useCallback, useState } from 'react';

import { setAuthToken, getAuthToken, clearAuthStorage } from '@/lib/authStorage';
import { AUTH_TOKEN_TTL_MS, COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from '@/lib/constants';

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

function setCookie(name: string, value: string, maxAgeSec: number): void {
  if (typeof document !== 'undefined') {
    const secure = window.location.protocol === 'https:' ? ';Secure' : '';
    document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=${maxAgeSec};SameSite=Lax${secure}`;
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
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ phone: input.phone, pin: input.pin }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = (await response.json()) as LoginResponse;

    // authStorage.ts kanonik kaynak — TTL'li JSON formatında saklanır
    setAuthToken(data.access_token, AUTH_TOKEN_TTL_MS);

    // Middleware ta_token ve ta_role cookie'lerini okur.
    // KR-063: Cookie'ye rol grubunu yazıyoruz (middleware ROLE_PREFIXES grup bazlı).
    const maxAgeSec = Math.floor(AUTH_TOKEN_TTL_MS / 1000);
    setCookie(COOKIE_TOKEN_KEY, data.access_token, maxAgeSec);
    const roleGroup = ROLE_TO_GROUP[data.user.role] ?? 'farmer';
    setCookie(COOKIE_ROLE_KEY, roleGroup, maxAgeSec);

    setState({ token: data.access_token, user: data.user });
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
