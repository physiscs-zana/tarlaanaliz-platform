/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: QC ciktilari contract-first dogrulama adimlarina baglanir. */
/* KR-018: kalibrasyon hard-gate gorunurlugu. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
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

export default function AdminMonitoringPage() {
  const [qcItems, setQcItems] = useState<QcItem[]>([]);
  const [calItems, setCalItems] = useState<CalibrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [qcRes, calRes] = await Promise.all([
        fetch(`${baseUrl}/qc/reports`, { headers }),
        fetch(`${baseUrl}/calibration/records`, { headers }),
      ]);

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
    } catch { setError("Izleme verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Izleme</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sol: QC Kontrol */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-600">QC Kontrol</h2>
          {qcItems.length === 0 ? (
            <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-10 text-center">
              <p className="text-sm font-medium text-slate-500">QC kuyrugunda bekleyen dogrulama yok.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-slate-100 bg-slate-50">
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
                      <td className="px-3 py-2">{item.status}</td>
                      <td className="px-3 py-2 text-xs text-slate-500">{item.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Sag: Kalibrasyon */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-600">Kalibrasyon Izleme</h2>
          {calItems.length === 0 ? (
            <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-10 text-center">
              <p className="text-sm font-medium text-slate-500">Kalibrasyon bekleyen gorev yok.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-slate-100 bg-slate-50">
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
                      <td className="px-3 py-2">{item.drone_id}</td>
                      <td className="px-3 py-2">{item.status}</td>
                      <td className="px-3 py-2 text-xs text-slate-500">{item.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
