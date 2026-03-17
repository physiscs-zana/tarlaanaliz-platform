/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role/auth guard akışında izlenebilir yönlendirme. */

import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "@/lib/constants";
import { LogoutButton } from "@/components/common/LogoutButton";

interface AdminLayoutProps {
  readonly children: ReactNode;
}

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analytics", label: "Analitik" },
  { href: "/users", label: "Kullanicilar" },
  { href: "/expert-management", label: "Uzmanlar" },
  { href: "/pilots", label: "Pilotlar" },
  { href: "/price-management", label: "Fiyatlandirma" },
  { href: "/admin/payments", label: "Odemeler" },
  { href: "/admin/sla", label: "SLA" },
  { href: "/audit", label: "Denetim Kayitlari" },
  { href: "/calibration", label: "Kalibrasyon" },
  { href: "/qc", label: "Kalite Kontrol" },
  { href: "/api-keys", label: "API Anahtarlari" },
] as const;

export default function AdminLayout({ children }: AdminLayoutProps) {
  const cookieStore = cookies();
  const token = cookieStore.get(COOKIE_TOKEN_KEY)?.value;
  const role = cookieStore.get(COOKIE_ROLE_KEY)?.value;

  if (!token) {
    redirect("/login");
  }

  // KR-063: admin grubu rolleri — CENTRAL_ADMIN, BILLING_ADMIN, IL_OPERATOR, STATION_OPERATOR
  if (role !== "admin") {
    redirect("/forbidden");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 md:grid-cols-[240px_1fr]">
        <aside className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-600">Admin</h2>
          <nav aria-label="Admin navigation" className="space-y-2">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} className="block rounded px-2 py-1 text-sm hover:bg-slate-100">
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-4 border-t border-slate-100 pt-3">
            <LogoutButton />
          </div>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}
