/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Uzman inceleme kuyrugu — API'den cekilir, gorev yoksa bos durum gosterilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface QueueItem {
  review_id: string;
  mission_id: string;
  field_name: string;
  priority: string;
  status: string;
  band_class: string;
  report_tier: string;
}

const PRIORITY_LABELS: Record<string, { label: string; className: string }> = {
  high: { label: "Yuksek", className: "bg-rose-100 text-rose-800" },
  medium: { label: "Orta", className: "bg-amber-100 text-amber-800" },
  low: { label: "Dusuk", className: "bg-slate-100 text-slate-600" },
};

export default function ExpertQueuePage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/expert-portal/queue`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Kuyruk yuklenemedi");
      const data = (await res.json()) as QueueItem[];
      setItems(data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Inceleme Kuyrugu</h1>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : items.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ GOREV YOK</p>
          <p className="mt-2 text-sm text-slate-400">Incelenecek gorev geldiginde burada gorunecektir.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="p-3">Inceleme</th>
                <th className="p-3">Gorev</th>
                <th className="p-3">Tarla</th>
                <th className="p-3">Oncelik</th>
                <th className="p-3">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const prio = PRIORITY_LABELS[item.priority] ?? { label: item.priority, className: "bg-slate-100 text-slate-600" };
                return (
                  <tr key={item.review_id} className="border-b last:border-0">
                    <td className="p-3 font-mono text-xs">{item.review_id.slice(0, 12)}</td>
                    <td className="p-3 font-mono text-xs">{item.mission_id.slice(0, 12)}</td>
                    <td className="p-3">{item.field_name}</td>
                    <td className="p-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${prio.className}`}>{prio.label}</span>
                    </td>
                    <td className="p-3">
                      <Link href={`/review/${item.review_id}`} className="rounded border px-2 py-1 text-xs hover:bg-slate-50">Ac</Link>
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
