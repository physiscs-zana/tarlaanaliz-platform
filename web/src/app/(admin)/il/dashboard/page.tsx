/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-083: Il Operatoru KPI + kapasite metrikleri — il bazli veriler. */
/* KR-066: PII GORMEZ — yalnizca FieldID/ozet KPI gorunur. */

"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface ProvinceData {
  province: string;
  total_fields: number;
  total_subscriptions: number;
  active_missions: number;
  completed_missions: number;
  total_revenue_kurus: number;
  active_pilots: number;
}

export default function IlDashboardPage() {
  const [provinces, setProvinces] = useState<ProvinceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [totals, setTotals] = useState({ fields: 0, subscriptions: 0, activeMissions: 0, completed: 0, revenue: 0, pilots: 0 });

  useEffect(() => {
    const token = getTokenFromCookie();
    if (!token) return;
    fetch(`${getApiBaseUrl()}/admin/province-stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : { provinces: [] }))
      .then((data) => {
        const list: ProvinceData[] = data.provinces || [];
        setProvinces(list);
        setTotals({
          fields: list.reduce((s, p) => s + p.total_fields, 0),
          subscriptions: list.reduce((s, p) => s + p.total_subscriptions, 0),
          activeMissions: list.reduce((s, p) => s + p.active_missions, 0),
          completed: list.reduce((s, p) => s + p.completed_missions, 0),
          revenue: list.reduce((s, p) => s + p.total_revenue_kurus, 0),
          pilots: list.reduce((s, p) => s + p.active_pilots, 0),
        });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const fmt = (v: number) => v.toLocaleString("tr-TR");
  const fmtTL = (kurus: number) => (kurus / 100).toLocaleString("tr-TR", { minimumFractionDigits: 2 });

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Il Operatoru Dashboard</h1>
      <p className="text-xs text-amber-600">
        KR-066: Bu ekranda kisisel veriler (PII) gosterilmez. Yalnizca ozet KPI ve kapasite metrikleri goruntulenir.
      </p>

      {/* Ozet Metrikler */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        {[
          { label: "Toplam Tarla", value: fmt(totals.fields), color: "text-emerald-600" },
          { label: "Abonelik", value: fmt(totals.subscriptions), color: "text-blue-600" },
          { label: "Aktif Gorev", value: fmt(totals.activeMissions), color: "text-amber-600" },
          { label: "Tamamlanan", value: fmt(totals.completed), color: "text-green-600" },
          { label: "Toplam Gelir", value: `${fmtTL(totals.revenue)} TL`, color: "text-purple-600" },
          { label: "Aktif Pilot", value: fmt(totals.pilots), color: "text-slate-600" },
        ].map((m) => (
          <div key={m.label} className="rounded-lg border border-slate-200 bg-white p-4 text-center">
            <p className={`text-2xl font-bold ${m.color}`}>{loading ? "\u2014" : m.value}</p>
            <p className="mt-1 text-xs text-slate-500">{m.label}</p>
          </div>
        ))}
      </div>

      {/* Il Bazli Tablo */}
      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-4 py-3">
          <h2 className="font-medium text-slate-900">Il Bazli Veriler</h2>
        </div>
        {loading ? (
          <div className="p-6 text-center text-sm text-slate-500">Yukleniyor...</div>
        ) : provinces.length === 0 ? (
          <div className="p-6 text-center text-sm text-slate-500">Henuz il verisi bulunmuyor.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-left">
                  <th className="px-4 py-2 font-medium text-slate-600">Il</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Tarla</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Abonelik</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Aktif Gorev</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Tamamlanan</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Gelir (TL)</th>
                  <th className="px-4 py-2 font-medium text-slate-600 text-right">Pilot</th>
                </tr>
              </thead>
              <tbody>
                {provinces.map((p) => (
                  <tr key={p.province} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="px-4 py-2 font-medium text-slate-900">{p.province}</td>
                    <td className="px-4 py-2 text-right">{fmt(p.total_fields)}</td>
                    <td className="px-4 py-2 text-right">{fmt(p.total_subscriptions)}</td>
                    <td className="px-4 py-2 text-right">{fmt(p.active_missions)}</td>
                    <td className="px-4 py-2 text-right">{fmt(p.completed_missions)}</td>
                    <td className="px-4 py-2 text-right">{fmtTL(p.total_revenue_kurus)}</td>
                    <td className="px-4 py-2 text-right">{fmt(p.active_pilots)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
