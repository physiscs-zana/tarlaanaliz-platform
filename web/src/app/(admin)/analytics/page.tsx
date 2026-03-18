/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: corr/request trace bilgileri UI metadata alanlarinda tasinir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface AnalyticsMetrics {
  total_analyses: number | null;
  active_experts: number | null;
  pending_reviews: number | null;
  sla_compliance: number | null;
}

export default function AdminAnalyticsPage() {
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/analytics`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as AnalyticsMetrics;
        setMetrics(data);
      }
    } catch { setError("Analitik verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  if (error) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      </section>
    );
  }

  if (!metrics || (metrics.total_analyses === null && metrics.active_experts === null && metrics.pending_reviews === null && metrics.sla_compliance === null)) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Analitik verileri islemler gerceklestikce burada gorunecektir.</p>
        </div>
      </section>
    );
  }

  const metricCards = [
    { label: "Toplam Analiz", value: metrics.total_analyses?.toLocaleString("tr-TR") ?? "—" },
    { label: "Aktif Expert", value: metrics.active_experts?.toLocaleString("tr-TR") ?? "—" },
    { label: "Bekleyen Inceleme", value: metrics.pending_reviews?.toLocaleString("tr-TR") ?? "—" },
    { label: "SLA Uyum", value: metrics.sla_compliance !== null ? `%${metrics.sla_compliance}` : "—" },
  ];

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((card) => (
          <article key={card.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-600">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{card.value}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
