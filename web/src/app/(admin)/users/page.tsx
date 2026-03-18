/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-063: Admin user listing. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface UserItem {
  user_id: string;
  phone: string;
  display_name: string;
  role: string;
  province: string;
  district: string;
  active: boolean;
}

const ROLE_LABELS: Record<string, string> = {
  FARMER_SINGLE: "Ciftci",
  PILOT: "Pilot",
  EXPERT: "Uzman",
  CENTRAL_ADMIN: "Admin",
  BILLING_ADMIN: "Odeme Yoneticisi",
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Kullanici Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">{users.length} kayitli kullanici</p>
        </div>
      </div>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {users.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">Kayitli kullanici bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Ad Soyad</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Telefon</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Rol</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Il / Ilce</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {users.map((u) => (
                <tr key={u.user_id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-medium text-slate-900">{u.display_name || "—"}</td>
                  <td className="px-4 py-2.5 font-mono text-xs">{u.phone}</td>
                  <td className="px-4 py-2.5">
                    <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      {ROLE_LABELS[u.role] ?? u.role}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">
                    {u.province || "—"}{u.district ? ` / ${u.district}` : ""}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${u.active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                      {u.active ? "Aktif" : "Pasif"}
                    </span>
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
