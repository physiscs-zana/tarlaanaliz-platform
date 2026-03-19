/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: QC ciktilari contract-first dogrulama adimlarina baglanir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface QcItem {
  qc_id: string;
  dataset_id: string;
  status: string;
  created_at: string;
}

export default function AdminQcPage() {
  const [items, setItems] = useState<QcItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQc = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/qc/reports`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const raw = await res.json();
        const arr = Array.isArray(raw) ? raw : (raw.items ?? raw.reports ?? []);
        setItems(arr.map((r: Record<string, string>) => ({
          qc_id: r.report_id ?? r.qc_id ?? "",
          dataset_id: r.dataset_id ?? r.field_id ?? "",
          status: r.decision ?? r.status ?? "",
          created_at: r.created_at ?? "",
        })));
      }
    } catch { setError("QC verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchQc(); }, [fetchQc]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">QC Kontrol</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {items.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">QC kuyrugunda bekleyen dogrulama bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">QC ID</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Dataset</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Tarih</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {items.map((item) => (
                <tr key={item.qc_id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs">{item.qc_id}</td>
                  <td className="px-4 py-2.5 font-mono text-xs">{item.dataset_id}</td>
                  <td className="px-4 py-2.5">{item.status}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{item.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
