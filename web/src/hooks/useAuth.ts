// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: Auth artefact lifecycle — authStorage.ts kanonik kaynaktır.
'use client';

import { useCallback, useState } from 'react';

import { setAuthToken, getAuthToken, clearAuthStorage } from '@/lib/authStorage';
import { AUTH_TOKEN_TTL_MS, COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from '@/lib/constants';

export type AuthRole = 'farmer' | 'expert' | 'pilot' | 'admin';

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

    // Middleware ta_token ve ta_role cookie'lerini okur
    const maxAgeSec = Math.floor(AUTH_TOKEN_TTL_MS / 1000);
    setCookie(COOKIE_TOKEN_KEY, data.access_token, maxAgeSec);
    setCookie(COOKIE_ROLE_KEY, data.user.role, maxAgeSec);

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
