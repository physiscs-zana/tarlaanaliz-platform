/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif uye yonetimi — listeleme. */
/* KR-063: Erisim: COOP_OWNER, COOP_ADMIN rolleri. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface CoopMember {
  readonly id: string;
  readonly name: string;
  readonly phone: string;
  readonly status: "ACTIVE" | "PENDING" | "INACTIVE";
  readonly role: string;
}

const STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  ACTIVE: { label: "Aktif", cls: "bg-emerald-50 text-emerald-700" },
  PENDING: { label: "Onay Bekliyor", cls: "bg-amber-50 text-amber-700" },
  INACTIVE: { label: "Pasif", cls: "bg-slate-100 text-slate-500" },
};

const ROLE_LABEL: Record<string, string> = {
  COOP_OWNER: "Kooperatif Sahibi",
  COOP_ADMIN: "Kooperatif Admin",
  COOP_AGRONOMIST: "Agronomist",
  COOP_VIEWER: "Izleyici",
  FARMER_MEMBER: "Uye Ciftci",
  FARMER_SINGLE: "Ciftci",
};

export default function CoopMembersPage() {
  const [members, setMembers] = useState<readonly CoopMember[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMembers = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/coop/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as CoopMember[];
        setMembers(data ?? []);
      }
    } catch { /* noop */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchMembers(); }, [fetchMembers]);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Kooperatif Uyeleri</h1>
        <a href="/coop/invite" className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">
          Uye Davet Et
        </a>
      </div>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : members.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
          <p className="text-sm text-slate-500">Henuz uye bulunmuyor. Uye davet etmek icin butonu kullanin.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Ad</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Telefon</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Rol</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {members.map((m) => {
                const si = STATUS_LABEL[m.status] ?? { label: m.status, cls: "bg-slate-100 text-slate-600" };
                return (
                  <tr key={m.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-800">{m.name || "---"}</td>
                    <td className="px-3 py-2 text-slate-600 font-mono text-xs">{m.phone}</td>
                    <td className="px-3 py-2 text-slate-600">{ROLE_LABEL[m.role] ?? m.role}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${si.cls}`}>{si.label}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
