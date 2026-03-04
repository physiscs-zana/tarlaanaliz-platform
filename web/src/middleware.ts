/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: auth + role yönlendirmesi güvenli varsayılanla uygulanır. */

import { NextRequest, NextResponse } from "next/server";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "./lib/constants";

const PUBLIC_PATHS = new Set(["/login", "/register", "/", "/api/health", "/forbidden"]);
const ROLE_PREFIXES: Record<string, readonly string[]> = {
  admin: ["/analytics", "/audit", "/audit-viewer", "/pricing", "/price-management", "/admin/sla", "/users", "/admin/payments", "/calibration", "/qc", "/api-keys", "/experts", "/expert-management", "/pilots", "/dashboard"],
  expert: ["/queue", "/review", "/reviews", "/expert/settings", "/expert/sla", "/expert/profile"],
  farmer: ["/fields", "/missions", "/subscriptions", "/results", "/payments", "/profile"],
  pilot: ["/pilot/missions", "/planner", "/capacity", "/weather-block", "/pilot/settings", "/pilot/profile"],
};

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
