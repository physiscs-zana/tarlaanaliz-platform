/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role/auth guard akışında izlenebilir yönlendirme. */

import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { COOKIE_TOKEN_KEY, COOKIE_ROLE_KEY } from "@/lib/constants";

interface ExpertLayoutProps {
  readonly children: ReactNode;
}

export default function ExpertLayout({ children }: ExpertLayoutProps) {
  const cookieStore = cookies();
  const token = cookieStore.get(COOKIE_TOKEN_KEY)?.value;
  const role = cookieStore.get(COOKIE_ROLE_KEY)?.value;

  if (!token) {
    redirect("/login");
  }

  if (role !== "expert") {
    redirect("/forbidden");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <nav className="mx-auto flex max-w-6xl gap-4 px-4 py-3" aria-label="Expert navigation">
          <Link href="/queue" className="rounded px-2 py-1 text-sm hover:bg-slate-100">
            Kuyruk
          </Link>
          <Link href="/reviews" className="rounded px-2 py-1 text-sm hover:bg-slate-100">
            İncelemelerim
          </Link>
          <Link href="/expert/profile" className="rounded px-2 py-1 text-sm hover:bg-slate-100">
            Profil
          </Link>
          <Link href="/expert/settings" className="rounded px-2 py-1 text-sm hover:bg-slate-100">
            Ayarlar
          </Link>
          <Link href="/expert/sla" className="rounded px-2 py-1 text-sm hover:bg-slate-100">
            SLA
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
