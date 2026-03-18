/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role/auth guard akışında izlenebilir yönlendirme. */

import type { ReactNode } from "react";
import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "@/lib/constants";
import { LogoutButton } from "@/components/common/LogoutButton";

interface PilotLayoutProps {
  readonly children: ReactNode;
}

const navItems = [
  { href: "/pilot/missions", label: "Görevler" },
  { href: "/planner", label: "Planlayıcı" },
  { href: "/weather-block", label: "Hava Engeli" },
  { href: "/pilot/settings", label: "Ayarlar" },
  { href: "/pilot/profile", label: "Profil" },
] as const;

export default function PilotLayout({ children }: PilotLayoutProps) {
  const store = cookies();
  const token = store.get(COOKIE_TOKEN_KEY)?.value;
  const role = store.get(COOKIE_ROLE_KEY)?.value;

  if (!token) redirect("/login");
  if (role !== "pilot") redirect("/forbidden");

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-600">Pilot</h2>
          <nav className="space-y-2" aria-label="Pilot navigation">
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
