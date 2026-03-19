/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-018: kalibrasyon hard-gate gorunurlugu. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface CalibrationItem {
  mission_id: string;
  drone_id: string;
  status: string;
  date: string;
}

export default function AdminCalibrationPage() {
  const [items, setItems] = useState<CalibrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCalibration = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/calibration/records`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const raw = await res.json();
        const arr = Array.isArray(raw) ? raw : (raw.items ?? raw.records ?? []);
        setItems(arr.map((r: Record<string, string>) => ({
          mission_id: r.record_id ?? r.mission_id ?? "",
          drone_id: r.drone_id ?? "",
          status: r.status ?? r.calibration_type ?? "",
          date: r.captured_at ?? r.date ?? r.created_at ?? "",
        })));
      }
    } catch { setError("Kalibrasyon verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchCalibration(); }, [fetchCalibration]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Kalibrasyon Izleme</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {items.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Kalibrasyon bekleyen gorev bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Gorev ID</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Drone</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Tarih</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {items.map((item) => (
                <tr key={item.mission_id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs">{item.mission_id}</td>
                  <td className="px-4 py-2.5">{item.drone_id}</td>
                  <td className="px-4 py-2.5">{item.status}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{item.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
