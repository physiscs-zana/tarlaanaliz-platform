/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: auth + role yönlendirmesi güvenli varsayılanla uygulanır. */
/* KR-062: Tek kaynak gerçek — route tanımları routes.ts'den import edilir. */

import { NextRequest, NextResponse } from "next/server";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "./lib/constants";
import { PUBLIC_PATHS, ROLE_PREFIXES } from "./lib/routes";

function isStaticPath(pathname: string): boolean {
  return pathname.startsWith("/_next") || pathname.startsWith("/icons") || pathname.startsWith("/sounds") || pathname.includes(".");
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isStaticPath(pathname) || PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next();
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

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};
