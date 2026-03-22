/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme/onay adimlarinda audit gorunurlugu + SLA izleme. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface AuditEntry {
  timestamp: string;
  user: string;
  action: string;
  status: string;
}

interface SlaMetrics {
  review_start_sla_hours: number | null;
  decision_sla_hours: number | null;
  compliance_rate: number | null;
}

export default function AuditAndSlaPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [sla, setSla] = useState<SlaMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [auditRes, slaRes] = await Promise.all([
        fetch(`${baseUrl}/admin/audit/logs`, { headers }),
        fetch(`${baseUrl}/admin/sla`, { headers }),
      ]);

      if (auditRes.ok) {
        const data = await auditRes.json();
        const items = (data.items ?? data) as Array<Record<string, string>>;
        setEntries(
          items.map((item) => ({
            timestamp: item.occurred_at ?? item.timestamp ?? "",
            user: item.actor_subject ?? item.user ?? "",
            action: item.action ?? "",
            status: item.resource ?? item.status ?? "",
          }))
        );
      }

      if (slaRes.ok) {
        setSla(await slaRes.json());
      }
    } catch {
      setError("Veriler yuklenemedi.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Denetim Kayitlari ve SLA</h1>
        <p className="text-sm text-slate-500">Islem gecmisi ve hizmet seviyesi metrikleri.</p>
      </div>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {/* SLA Metrikleri — 3 kart yan yana */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-blue-600">
            {sla?.review_start_sla_hours != null ? `${sla.review_start_sla_hours}s` : "\u2014"}
          </p>
          <p className="mt-1 text-xs text-slate-500">Inceleme Baslangic SLA</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-amber-600">
            {sla?.decision_sla_hours != null ? `${sla.decision_sla_hours}s` : "\u2014"}
          </p>
          <p className="mt-1 text-xs text-slate-500">Karar SLA</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className={`text-3xl font-bold ${sla?.compliance_rate != null && sla.compliance_rate >= 90 ? "text-emerald-600" : sla?.compliance_rate != null ? "text-red-600" : "text-slate-400"}`}>
            {sla?.compliance_rate != null ? `%${sla.compliance_rate}` : "\u2014"}
          </p>
          <p className="mt-1 text-xs text-slate-500">SLA Uyum Orani</p>
        </div>
      </div>

      {/* Denetim Kayitlari Tablosu */}
      {entries.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
          <p className="text-lg font-medium text-slate-500">Henuz denetim kaydi bulunmuyor.</p>
          <p className="mt-2 text-sm text-slate-400">Islemler gerceklestikce burada gorunecektir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="max-h-[480px] overflow-y-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 border-b border-slate-100 bg-slate-50">
                <tr>
                  <th className="px-3 py-2 font-medium text-slate-600">Zaman</th>
                  <th className="px-3 py-2 font-medium text-slate-600">Kullanici</th>
                  <th className="px-3 py-2 font-medium text-slate-600">Islem</th>
                  <th className="px-3 py-2 font-medium text-slate-600">Kaynak</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {entries.map((entry, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "\u2014"}
                    </td>
                    <td className="px-3 py-2 text-xs font-mono">{entry.user || "\u2014"}</td>
                    <td className="px-3 py-2 text-xs">{entry.action}</td>
                    <td className="px-3 py-2 text-xs">{entry.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
