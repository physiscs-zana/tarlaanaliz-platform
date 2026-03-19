/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-063: Admin user listing — farmers with field/parcel info. */

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

type SortKey = "display_name" | "phone" | "province" | "active";
type SortDir = "asc" | "desc";

interface FieldInfo {
  field_code: string;
  block_no: string;
  parcel_no: string;
  village: string;
  crop_type: string | null;
  area_donum: number | null;
}

interface UserItem {
  user_id: string;
  phone: string;
  display_name: string;
  province: string;
  district: string;
  active: boolean;
  fields: FieldInfo[];
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("display_name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortedUsers = useMemo(() => {
    return [...users].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "boolean") {
        return sortDir === "asc"
          ? (aVal === bVal ? 0 : aVal ? -1 : 1)
          : (aVal === bVal ? 0 : aVal ? 1 : -1);
      }
      const aStr = (aVal ?? "").toString().toLocaleLowerCase("tr");
      const bStr = (bVal ?? "").toString().toLocaleLowerCase("tr");
      const cmp = aStr.localeCompare(bStr, "tr");
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [users, sortKey, sortDir]);

  const sortIndicator = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : "";

  const fetchUsers = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as UserItem[];
        setUsers(data ?? []);
      }
    } catch { setError("Kullanici listesi yuklenemedi."); } finally { setLoading(false); }
  }, []);

  const handleDelete = async (userId: string) => {
    if (!window.confirm("Bu ciftciyi silmek istediginize emin misiniz?")) return;
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok || res.status === 204) {
        setUsers((prev) => prev.filter((u) => u.user_id !== userId));
      }
    } catch { /* ignore */ }
  };

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Ciftci Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">{users.length} kayitli ciftci</p>
        </div>
      </div>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {users.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">Kayitli ciftci bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600 cursor-pointer select-none" onClick={() => handleSort("display_name")}>Ad Soyad{sortIndicator("display_name")}</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 cursor-pointer select-none" onClick={() => handleSort("phone")}>Telefon{sortIndicator("phone")}</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Ada / Parsel</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 cursor-pointer select-none" onClick={() => handleSort("province")}>Il / Ilce{sortIndicator("province")}</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 cursor-pointer select-none" onClick={() => handleSort("active")}>Durum{sortIndicator("active")}</th>
                <th className="px-4 py-2 text-right font-medium text-slate-600">Islem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {sortedUsers.map((u) => (
                <tr key={u.user_id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-medium text-slate-900">{u.display_name || "\u2014"}</td>
                  <td className="px-4 py-2.5 font-mono text-xs">{u.phone}</td>
                  <td className="px-4 py-2.5">
                    {u.fields.length === 0 ? (
                      <span className="text-xs text-slate-400">Tarla yok</span>
                    ) : (
                      <div className="space-y-0.5">
                        {u.fields.map((f) => (
                          <div key={f.field_code} className="text-xs">
                            <span className="font-mono text-slate-700">{f.block_no}/{f.parcel_no}</span>
                            <span className="ml-1.5 text-slate-400">{f.village}</span>
                            {f.crop_type && <span className="ml-1.5 rounded bg-emerald-50 px-1 py-0.5 text-emerald-700">{f.crop_type}</span>}
                            {f.area_donum != null && <span className="ml-1 text-slate-400">{f.area_donum}d</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">
                    {u.province || "\u2014"}{u.district ? ` / ${u.district}` : ""}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${u.active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                      {u.active ? "Aktif" : "Pasif"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button onClick={() => handleDelete(u.user_id)} className="rounded bg-rose-50 px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-100">Sil</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
