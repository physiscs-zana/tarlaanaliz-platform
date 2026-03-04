/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: role tabanlı yönlendirme stub akışı. */

import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { COOKIE_ROLE_KEY } from "@/lib/constants";

export default function HomePage() {
  const store = cookies();
  const role = store.get(COOKIE_ROLE_KEY)?.value;

  if (role === "admin") redirect("/analytics");
  if (role === "expert") redirect("/queue");
  if (role === "farmer") redirect("/fields");
  if (role === "pilot") redirect("/pilot/missions");

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-3xl font-semibold">TarlaAnaliz Platform</h1>
      <p className="text-slate-600">Rol bazlı akışlar için giriş yapın.</p>
      <Link href="/login" className="rounded bg-slate-900 px-4 py-2 text-sm text-white">
        Girişe Git
      </Link>
    </main>
  );
}
