/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif dashboard — uye sayisi, tarla sayisi, aktif gorev ozeti. */
/* KR-063: Erisim: COOP_OWNER, COOP_ADMIN rolleri. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface DashboardData {
  member_count: number;
  field_count: number;
  mission_count: number;
}

interface CoopInfo {
  coop_id: string;
  name: string;
  province: string;
  district: string | null;
  status: string;
  owner_display_name: string | null;
  member_count: number;
}

export default function CoopDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [coop, setCoop] = useState<CoopInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [dashRes, coopRes] = await Promise.all([
        fetch(`${baseUrl}/coop/dashboard`, { headers }),
        fetch(`${baseUrl}/cooperatives/my`, { headers }),
      ]);
      if (dashRes.ok) setDashboard(await dashRes.json() as DashboardData);
      if (coopRes.ok) setCoop(await coopRes.json() as CoopInfo);
    } catch { /* noop */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
    PENDING_APPROVAL: { label: "Onay Bekliyor", cls: "bg-amber-100 text-amber-800" },
    ACTIVE: { label: "Aktif", cls: "bg-emerald-100 text-emerald-800" },
    SUSPENDED: { label: "Askiya Alindi", cls: "bg-rose-100 text-rose-800" },
  };

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Kooperatif Dashboard</h1>

      {coop && (
        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">{coop.name}</h2>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_LABELS[coop.status]?.cls ?? "bg-slate-100 text-slate-600"}`}>
              {STATUS_LABELS[coop.status]?.label ?? coop.status}
            </span>
          </div>
          <div className="flex gap-4 text-sm text-slate-500">
            <span>{coop.province}{coop.district ? ` / ${coop.district}` : ""}</span>
            {coop.owner_display_name && <span>Sahip: {coop.owner_display_name}</span>}
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">{dashboard?.member_count ?? "—"}</p>
          <p className="mt-1 text-sm text-slate-500">Toplam Uye</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">{dashboard?.field_count ?? "—"}</p>
          <p className="mt-1 text-sm text-slate-500">Toplam Tarla</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">{dashboard?.mission_count ?? "—"}</p>
          <p className="mt-1 text-sm text-slate-500">Aktif Gorev</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium mb-2">Hizli Erisim</h2>
        <nav className="flex gap-3 text-sm">
          <a href="/coop/members" className="text-sky-600 hover:underline">Uyeler</a>
          <a href="/coop/invite" className="text-sky-600 hover:underline">Davet Et</a>
          <a href="/coop/fields" className="text-sky-600 hover:underline">Tarlalar</a>
          <a href="/fields" className="text-sky-600 hover:underline">Tarla Ekle</a>
        </nav>
      </div>
    </section>
  );
}
