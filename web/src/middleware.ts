/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: auth + role yönlendirmesi güvenli varsayılanla uygulanır. */
/* KR-062: Tek kaynak gerçek — route tanımları routes.ts'den import edilir. */
/* SEC: Nonce-based CSP — eliminates unsafe-inline for scripts. */

import { NextRequest, NextResponse } from "next/server";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "./lib/constants";
import { PUBLIC_PATHS, ROLE_PREFIXES } from "./lib/routes";

function isStaticPath(pathname: string): boolean {
  return pathname.startsWith("/_next") || pathname.startsWith("/icons") || pathname.startsWith("/sounds") || pathname.includes(".");
}

/** Generate a cryptographic nonce (128-bit, base64). */
function generateNonce(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  // Convert to base64 without padding
  let binary = "";
  for (const byte of array) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=+$/, "");
}

function buildCspHeader(nonce: string): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.tarlaanaliz.com";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`,
    `style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src 'self' ${apiUrl}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Generate nonce for every request (including static for CSP header)
  const nonce = generateNonce();

  if (isStaticPath(pathname) || PUBLIC_PATHS.has(pathname)) {
    const response = NextResponse.next({
      request: { headers: new Headers({ ...Object.fromEntries(request.headers), "x-nonce": nonce }) },
    });
    response.headers.set("Content-Security-Policy", buildCspHeader(nonce));
    return response;
  }

  const token = request.cookies.get(COOKIE_TOKEN_KEY)?.value;
  const role = request.cookies.get(COOKIE_ROLE_KEY)?.value;

  if (!token || !role) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // SEC-FIX: Basic JWT format validation — a valid JWT has exactly 3
  // dot-separated base64url segments (header.payload.signature).
  const jwtParts = token.split(".");
  const base64urlRegex = /^[A-Za-z0-9_-]+$/;
  if (
    jwtParts.length !== 3 ||
    !jwtParts.every((part) => part.length > 0 && base64urlRegex.test(part))
  ) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete(COOKIE_TOKEN_KEY);
    response.cookies.delete(COOKIE_ROLE_KEY);
    return response;
  }

  const allowedPrefixes = ROLE_PREFIXES[role] ?? [];
  const isAllowed = allowedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));

  if (!isAllowed) {
    return NextResponse.redirect(new URL("/forbidden", request.url));
  }

  // Pass nonce to downstream via request header; set CSP on response
  const response = NextResponse.next({
    request: { headers: new Headers({ ...Object.fromEntries(request.headers), "x-nonce": nonce }) },
  });
  response.headers.set("Content-Security-Policy", buildCspHeader(nonce));
  return response;
}

export const config = {
  matcher: ["/:path*"],
};
