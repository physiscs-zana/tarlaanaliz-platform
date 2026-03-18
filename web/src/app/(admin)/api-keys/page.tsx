/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: key yonetim ekraninda trace metadata gorunur. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface ApiKeyItem {
  key_id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export default function AdminApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchKeys = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/api-keys`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as ApiKeyItem[];
        setKeys(data ?? []);
      }
    } catch { setError("API anahtarlari yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchKeys(); }, [fetchKeys]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">API Anahtarlari</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {keys.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Tanimlanmis API anahtari bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Ad</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Prefix</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Olusturulma</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Son Kullanim</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {keys.map((k) => (
                <tr key={k.key_id} className="hover:bg-slate-50">
                  <td className="px-4 py-2.5">{k.name}</td>
                  <td className="px-4 py-2.5 font-mono text-xs">{k.prefix}...</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{k.created_at}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{k.last_used_at ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
