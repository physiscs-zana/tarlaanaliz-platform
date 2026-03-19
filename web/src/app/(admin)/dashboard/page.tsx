/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface DashboardSummary {
  total_fields: number;
  active_missions: number;
  completed_analyses: number;
  pending_payments: number;
  total_users: number;
}

interface RecentActivity {
  time: string;
  action: string;
  detail: string;
}

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as { summary: DashboardSummary; recent_activities: RecentActivity[] };
        setSummary(data.summary ?? null);
        setActivities(data.recent_activities ?? []);
      }
    } catch { setError("Dashboard verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  if (error) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      </section>
    );
  }

  if (!summary) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Dashboard verileri sistem kullanildikca burada gorunecektir.</p>
        </div>
      </section>
    );
  }

  const summaryCards = [
    { label: "Toplam Tarla", value: summary.total_fields.toLocaleString("tr-TR") },
    { label: "Kayitli Kullanici", value: (summary.total_users ?? 0).toLocaleString("tr-TR") },
    { label: "Aktif Gorev", value: summary.active_missions.toLocaleString("tr-TR") },
    { label: "Tamamlanan Analiz", value: summary.completed_analyses.toLocaleString("tr-TR") },
    { label: "Bekleyen Odeme", value: summary.pending_payments.toLocaleString("tr-TR") },
  ];

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryCards.map((card) => (
          <article key={card.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{card.value}</p>
          </article>
        ))}
      </div>

      {activities.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-slate-700">Son Aktiviteler</h2>
          </div>
          <ul className="divide-y divide-slate-50">
            {activities.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3 px-4 py-3">
                <span className="mt-0.5 shrink-0 text-xs font-medium text-slate-400">{item.time}</span>
                <div>
                  <p className="text-sm font-medium text-slate-900">{item.action}</p>
                  <p className="text-xs text-slate-500">{item.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
