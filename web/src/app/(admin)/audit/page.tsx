/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme/onay adimlarinda audit gorunurlugu. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface AuditEntry {
  timestamp: string;
  user: string;
  action: string;
  status: string;
}

export default function AdminAuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAudit = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/audit`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as AuditEntry[];
        setEntries(data ?? []);
      }
    } catch { setError("Audit verileri yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAudit(); }, [fetchAudit]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit Loglari</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {entries.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Audit kayitlari islemler gerceklestikce burada gorunecektir.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="p-3">Zaman</th>
                <th className="p-3">Kullanici</th>
                <th className="p-3">Islem</th>
                <th className="p-3">Durum</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, idx) => (
                <tr key={idx} className="border-b">
                  <td className="p-3 text-xs">{entry.timestamp}</td>
                  <td className="p-3">{entry.user}</td>
                  <td className="p-3">{entry.action}</td>
                  <td className="p-3">{entry.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
