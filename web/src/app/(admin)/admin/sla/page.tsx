/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface SlaMetrics {
  review_start_sla_hours: number | null;
  decision_sla_hours: number | null;
  compliance_rate: number | null;
}

export default function AdminSlaPage() {
  const [metrics, setMetrics] = useState<SlaMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSla = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/sla`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as SlaMetrics;
        setMetrics(data);
      }
    } catch { setError("SLA verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchSla(); }, [fetchSla]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  if (error) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">SLA Izleme</h1>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      </section>
    );
  }

  if (!metrics || (metrics.review_start_sla_hours === null && metrics.decision_sla_hours === null && metrics.compliance_rate === null)) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">SLA Izleme</h1>
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">SLA metrikleri inceleme surecleri basladiginda burada gorunecektir.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">SLA Izleme</h1>
      <ul className="list-inside list-disc rounded-lg border border-slate-200 bg-white p-4 text-sm">
        {metrics.review_start_sla_hours !== null && <li>Inceleme baslangic SLA: &lt; {metrics.review_start_sla_hours} saat</li>}
        {metrics.decision_sla_hours !== null && <li>Karar SLA: &lt; {metrics.decision_sla_hours} saat</li>}
        {metrics.compliance_rate !== null && <li>Mevcut uyum: %{metrics.compliance_rate}</li>}
      </ul>
    </section>
  );
}
