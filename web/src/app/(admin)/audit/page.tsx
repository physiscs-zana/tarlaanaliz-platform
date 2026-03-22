/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme/onay adimlarinda audit gorunurlugu. */
/* KR-018: kalibrasyon hard-gate gorunurlugu. */
/* KR-081: QC ciktilari contract-first dogrulama adimlarina baglanir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
interface AuditEntry {
  timestamp: string;
  user: string;
  action: string;
  status: string;
}

interface QcItem {
  qc_id: string;
  dataset_id: string;
  status: string;
  created_at: string;
}

interface CalibrationItem {
  mission_id: string;
  drone_id: string;
  status: string;
  date: string;
}

const EmptyState = ({ message }: { message: string }) => (
  <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-8 text-center">
    <p className="text-sm text-slate-500">{message}</p>
  </div>
);

export default function AuditAndMonitoringPage() {
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [qcItems, setQcItems] = useState<QcItem[]>([]);
  const [calItems, setCalItems] = useState<CalibrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [auditRes, qcRes, calRes] = await Promise.all([
        fetch(`${baseUrl}/admin/audit/logs`, { headers }),
        fetch(`${baseUrl}/qc/reports`, { headers }),
        fetch(`${baseUrl}/calibration/records`, { headers }),
      ]);

      // Audit
      if (auditRes.ok) {
        const data = await auditRes.json();
        const items = (data.items ?? data) as Array<Record<string, string>>;
        setAuditEntries(
          items.map((item) => ({
            timestamp: item.occurred_at ?? item.timestamp ?? "",
            user: item.actor_subject ?? item.user ?? "",
            action: item.action ?? "",
            status: item.resource ?? item.status ?? "",
          }))
        );
      }

      // QC
      if (qcRes.ok) {
        const raw = await qcRes.json();
        const arr = Array.isArray(raw) ? raw : (raw.items ?? raw.reports ?? []);
        setQcItems(arr.map((r: Record<string, string>) => ({
          qc_id: r.report_id ?? r.qc_id ?? "",
          dataset_id: r.dataset_id ?? r.field_id ?? "",
          status: r.decision ?? r.status ?? "",
          created_at: r.created_at ?? "",
        })));
      }

      // Kalibrasyon
      if (calRes.ok) {
        const raw = await calRes.json();
        const arr = Array.isArray(raw) ? raw : (raw.items ?? raw.records ?? []);
        setCalItems(arr.map((r: Record<string, string>) => ({
          mission_id: r.record_id ?? r.mission_id ?? "",
          drone_id: r.drone_id ?? "",
          status: r.status ?? r.calibration_type ?? "",
          date: r.captured_at ?? r.date ?? r.created_at ?? "",
        })));
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
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Denetim ve Izleme</h1>
        <p className="text-sm text-slate-500">Audit kayitlari, QC kontrol ve kalibrasyon durumu.</p>
      </div>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ====== SOL: Denetim Kayitlari (Audit) ====== */}
        <div className="space-y-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
            Denetim Kayitlari
          </h2>
          {auditEntries.length === 0 ? (
            <EmptyState message="Henuz denetim kaydi bulunmuyor." />
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <div className="max-h-[520px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 border-b border-slate-100 bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-slate-600">Zaman</th>
                      <th className="px-3 py-2 text-left font-medium text-slate-600">Kullanici</th>
                      <th className="px-3 py-2 text-left font-medium text-slate-600">Islem</th>
                      <th className="px-3 py-2 text-left font-medium text-slate-600">Kaynak</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {auditEntries.map((entry, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
                          {entry.timestamp ? new Date(entry.timestamp).toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}
                        </td>
                        <td className="px-3 py-2 text-xs font-mono">{entry.user || "—"}</td>
                        <td className="px-3 py-2 text-xs">{entry.action}</td>
                        <td className="px-3 py-2 text-xs">{entry.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* ====== SAG: QC + Kalibrasyon ====== */}
        <div className="space-y-5">
          {/* QC Kontrol */}
          <div className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <span className="inline-block h-2 w-2 rounded-full bg-amber-500" />
              QC Kontrol
            </h2>
            {qcItems.length === 0 ? (
              <EmptyState message="QC kuyrugunda bekleyen dogrulama yok." />
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                <div className="max-h-[240px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 border-b border-slate-100 bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">QC ID</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Dataset</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Durum</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Tarih</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {qcItems.map((item) => (
                        <tr key={item.qc_id} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-mono text-xs">{item.qc_id}</td>
                          <td className="px-3 py-2 font-mono text-xs">{item.dataset_id}</td>
                          <td className="px-3 py-2 text-xs">{item.status}</td>
                          <td className="px-3 py-2 text-xs text-slate-500">{item.created_at}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Kalibrasyon Izleme */}
          <div className="space-y-3">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
              Kalibrasyon Izleme
            </h2>
            {calItems.length === 0 ? (
              <EmptyState message="Kalibrasyon bekleyen gorev yok." />
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
                <div className="max-h-[240px] overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 border-b border-slate-100 bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Gorev ID</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Drone</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Durum</th>
                        <th className="px-3 py-2 text-left font-medium text-slate-600">Tarih</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {calItems.map((item) => (
                        <tr key={item.mission_id} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-mono text-xs">{item.mission_id}</td>
                          <td className="px-3 py-2 text-xs">{item.drone_id}</td>
                          <td className="px-3 py-2 text-xs">{item.status}</td>
                          <td className="px-3 py-2 text-xs text-slate-500">{item.date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
