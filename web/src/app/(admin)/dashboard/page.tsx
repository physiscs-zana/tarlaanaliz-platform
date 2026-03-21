/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: corr/request trace bilgileri UI metadata alanlarinda tasinir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
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

interface AnalyticsMetrics {
  total_analyses: number | null;
  active_experts: number | null;
  pending_reviews: number | null;
  sla_compliance: number | null;
}

/* ------- Metric Card ------- */
function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </article>
  );
}

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [dashRes, analyticsRes] = await Promise.all([
        fetch(`${baseUrl}/admin/dashboard`, { headers }),
        fetch(`${baseUrl}/admin/analytics`, { headers }),
      ]);

      if (dashRes.ok) {
        const data = (await dashRes.json()) as { summary: DashboardSummary; recent_activities: RecentActivity[] };
        setSummary(data.summary ?? null);
        setActivities(data.recent_activities ?? []);
      }

      if (analyticsRes.ok) {
        const data = (await analyticsRes.json()) as AnalyticsMetrics;
        setMetrics(data);
      }
    } catch { setError("Veriler yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  if (error) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Genel Bakis</h1>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      </section>
    );
  }

  const hasDashboard = summary !== null;
  const hasAnalytics = metrics !== null && (
    metrics.total_analyses !== null || metrics.active_experts !== null ||
    metrics.pending_reviews !== null || metrics.sla_compliance !== null
  );

  if (!hasDashboard && !hasAnalytics) {
    return (
      <section className="space-y-6">
        <h1 className="text-2xl font-semibold">Genel Bakis</h1>
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ VERI-BILGI BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Veriler sistem kullanildikca burada gorunecektir.</p>
        </div>
      </section>
    );
  }

  const dashboardCards = summary ? [
    { label: "Toplam Tarla", value: summary.total_fields.toLocaleString("tr-TR") },
    { label: "Kayitli Kullanici", value: (summary.total_users ?? 0).toLocaleString("tr-TR") },
    { label: "Aktif Gorev", value: summary.active_missions.toLocaleString("tr-TR") },
    { label: "Tamamlanan Analiz", value: summary.completed_analyses.toLocaleString("tr-TR") },
    { label: "Bekleyen Odeme", value: summary.pending_payments.toLocaleString("tr-TR") },
  ] : [];

  const analyticsCards = metrics ? [
    { label: "Toplam Analiz", value: metrics.total_analyses?.toLocaleString("tr-TR") ?? "\u2014" },
    { label: "Aktif Expert", value: metrics.active_experts?.toLocaleString("tr-TR") ?? "\u2014" },
    { label: "Bekleyen Inceleme", value: metrics.pending_reviews?.toLocaleString("tr-TR") ?? "\u2014" },
    { label: "SLA Uyum", value: metrics.sla_compliance !== null ? `%${metrics.sla_compliance}` : "\u2014" },
  ] : [];

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Genel Bakis</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sol: Dashboard */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Dashboard</h2>
          {dashboardCards.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {dashboardCards.map((c) => <MetricCard key={c.label} label={c.label} value={c.value} />)}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Dashboard verisi yok.</p>
          )}

          {activities.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white">
              <div className="border-b border-slate-100 px-4 py-3">
                <h3 className="text-sm font-semibold text-slate-700">Son Aktiviteler</h3>
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
        </div>

        {/* Sag: Analitik */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Analitik</h2>
          {analyticsCards.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {analyticsCards.map((c) => <MetricCard key={c.label} label={c.label} value={c.value} />)}
            </div>
          ) : (
            <p className="text-sm text-slate-400">Analitik verisi yok.</p>
          )}
        </div>
      </div>
    </section>
  );
}
