/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface SlaData {
  avg_first_response_minutes: number | null;
  open_sla_risk_count: number | null;
}

export default function ExpertSlaPage() {
  const [sla, setSla] = useState<SlaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSla = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/expert-portal/sla`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setSla(null);
        return;
      }
      const data = (await res.json()) as SlaData;
      setSla(data);
    } catch {
      setError("SLA verileri yuklenemedi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSla(); }, [fetchSla]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">SLA Durumu</h1>
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : !sla || (sla.avg_first_response_minutes === null && sla.open_sla_risk_count === null) ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Henuz bir SLA durumunuz olusmamistir. Inceleme yapmaya basladiginizda SLA verileri burada gorunecektir.</p>
        </div>
      ) : (
        <ul className="list-inside list-disc rounded-lg border border-slate-200 bg-white p-4 text-sm">
          {sla.avg_first_response_minutes !== null && (
            <li>Ortalama ilk yanit: {Math.floor(sla.avg_first_response_minutes / 60)} saat {sla.avg_first_response_minutes % 60} dk</li>
          )}
          {sla.open_sla_risk_count !== null && (
            <li>Acik islerin SLA riski: {sla.open_sla_risk_count}</li>
          )}
        </ul>
      )}
    </section>
  );
}
