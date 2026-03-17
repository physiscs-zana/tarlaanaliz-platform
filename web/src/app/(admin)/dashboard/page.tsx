/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Admin Dashboard" };

const summaryCards = [
  { label: "Toplam Tarla", value: "3,412", trend: "+128 bu ay" },
  { label: "Aktif Görev", value: "87", trend: "14 uçuş bugün" },
  { label: "Tamamlanan Analiz", value: "1,284", trend: "+42 bu hafta" },
  { label: "Bekleyen Ödeme", value: "23", trend: "T+1 SLA" },
] as const;

const recentActivity = [
  { time: "14:32", action: "Yeni tarla kaydı", detail: "Diyarbakır / Bismil — 12.4 ha" },
  { time: "13:18", action: "Analiz tamamlandı", detail: "Görev #M-1042 — Pamuk hastalık tespiti" },
  { time: "12:45", action: "Expert inceleme", detail: "Dr. Ayşe K. — Karar: Onay" },
  { time: "11:30", action: "Ödeme onayı", detail: "850 TL — Dekont doğrulandı" },
  { time: "10:15", action: "Pilot kapasite", detail: "Ahmet D. — 3 slot müsait" },
] as const;

export default function AdminDashboardPage() {
  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <article key={card.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{card.value}</p>
            <p className="mt-0.5 text-xs text-slate-400">{card.trend}</p>
          </article>
        ))}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-700">Son Aktiviteler</h2>
        </div>
        <ul className="divide-y divide-slate-50">
          {recentActivity.map((item) => (
            <li key={item.time} className="flex items-start gap-3 px-4 py-3">
              <span className="mt-0.5 shrink-0 text-xs font-medium text-slate-400">{item.time}</span>
              <div>
                <p className="text-sm font-medium text-slate-900">{item.action}</p>
                <p className="text-xs text-slate-500">{item.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
