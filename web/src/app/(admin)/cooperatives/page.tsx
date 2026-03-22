/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Admin kooperatif yonetimi — onay bekleyen kooperatifleri listele ve onayla. */
/* KR-063: CENTRAL_ADMIN erisimi zorunlu. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface CoopItem {
  coop_id: string;
  name: string;
  province: string;
  district: string | null;
  status: string;
  owner_display_name: string | null;
  member_count: number;
  created_at: string;
}

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  PENDING_APPROVAL: { label: "Onay Bekliyor", cls: "bg-amber-50 text-amber-700" },
  ACTIVE: { label: "Aktif", cls: "bg-emerald-50 text-emerald-700" },
  SUSPENDED: { label: "Askiya Alindi", cls: "bg-rose-50 text-rose-700" },
};

export default function AdminCooperativesPage() {
  const [coops, setCoops] = useState<CoopItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCoops = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/cooperatives`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as CoopItem[];
        setCoops(data ?? []);
      }
    } catch { /* noop */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchCoops(); }, [fetchCoops]);

  const handleApprove = useCallback(async (coopId: string) => {
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/cooperatives/${coopId}/approve`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setCoops((prev) => prev.map((c) => (c.coop_id === coopId ? { ...c, status: "ACTIVE" } : c)));
      } else {
        const body = await res.json().catch(() => ({}));
        alert((body as { detail?: string }).detail || "Onay basarisiz.");
      }
    } catch { alert("Baglanti hatasi."); }
  }, []);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  const pending = coops.filter((c) => c.status === "PENDING_APPROVAL");
  const active = coops.filter((c) => c.status === "ACTIVE");
  const suspended = coops.filter((c) => c.status === "SUSPENDED");

  const renderTable = (items: CoopItem[], title: string, emptyMsg: string, showApprove: boolean) => (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold text-slate-700">{title} ({items.length})</h2>
      {items.length === 0 ? (
        <p className="text-sm text-slate-400">{emptyMsg}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Kooperatif</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Il / Ilce</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Sahip</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Uye</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Durum</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Tarih</th>
                {showApprove && <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Islem</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {items.map((c) => {
                const si = STATUS_LABELS[c.status] ?? { label: c.status, cls: "bg-slate-100 text-slate-600" };
                return (
                  <tr key={c.coop_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium text-slate-800">{c.name}</td>
                    <td className="px-3 py-2 text-slate-600">{c.province}{c.district ? ` / ${c.district}` : ""}</td>
                    <td className="px-3 py-2 text-slate-600">{c.owner_display_name ?? "---"}</td>
                    <td className="px-3 py-2 text-slate-700 font-medium">{c.member_count}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${si.cls}`}>{si.label}</span>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500">{new Date(c.created_at).toLocaleDateString("tr-TR")}</td>
                    {showApprove && (
                      <td className="px-3 py-2">
                        <button
                          type="button"
                          onClick={() => handleApprove(c.coop_id)}
                          className="rounded bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
                        >
                          Onayla
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Kooperatif Yonetimi</h1>
      {renderTable(pending, "Onay Bekleyen", "Onay bekleyen kooperatif yok.", true)}
      {renderTable(active, "Aktif Kooperatifler", "Aktif kooperatif yok.", false)}
      {renderTable(suspended, "Askiya Alinan", "Askiya alinan kooperatif yok.", false)}
    </section>
  );
}
