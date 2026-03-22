/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Uzman inceleme gecmisi — tamamlanmis incelemeleri listeler. */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface ReviewItem {
  review_id: string;
  mission_id: string;
  analysis_result_id: string;
  status: string;
  assigned_at: string;
  priority: number;
}

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  PENDING: { label: "Bekliyor", cls: "bg-amber-100 text-amber-800" },
  IN_PROGRESS: { label: "Inceleniyor", cls: "bg-blue-100 text-blue-800" },
  COMPLETED: { label: "Tamamlandi", cls: "bg-emerald-100 text-emerald-800" },
  REJECTED: { label: "Reddedildi", cls: "bg-rose-100 text-rose-800" },
};

export default function ExpertReviewsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReviews = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/expert-portal/reviews/queue?limit=100`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as ReviewItem[];
        setReviews(data ?? []);
      }
    } catch { /* noop */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchReviews(); }, [fetchReviews]);

  const completed = reviews.filter((r) => r.status === "COMPLETED" || r.status === "REJECTED");
  const active = reviews.filter((r) => r.status === "PENDING" || r.status === "IN_PROGRESS");

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Incelemelerim</h1>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : reviews.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ INCELEME BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Inceleme atamaniz yapildiginda burada gorunecektir.</p>
        </div>
      ) : (
        <>
          {/* Aktif incelemeler */}
          {active.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-amber-700">Aktif Incelemeler ({active.length})</h2>
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b bg-slate-50">
                    <tr>
                      <th className="p-3 font-medium text-slate-600">Inceleme</th>
                      <th className="p-3 font-medium text-slate-600">Gorev</th>
                      <th className="p-3 font-medium text-slate-600">Durum</th>
                      <th className="p-3 font-medium text-slate-600">Atanma</th>
                      <th className="p-3 font-medium text-slate-600">Aksiyon</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {active.map((r) => {
                      const si = STATUS_LABELS[r.status] ?? { label: r.status, cls: "bg-slate-100 text-slate-600" };
                      return (
                        <tr key={r.review_id} className="hover:bg-slate-50">
                          <td className="p-3 font-mono text-xs">{r.review_id.slice(0, 12)}</td>
                          <td className="p-3 font-mono text-xs">{r.mission_id.slice(0, 12)}</td>
                          <td className="p-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${si.cls}`}>{si.label}</span></td>
                          <td className="p-3 text-xs text-slate-500">{new Date(r.assigned_at).toLocaleString("tr-TR")}</td>
                          <td className="p-3">
                            <Link href={`/reviews/${r.review_id}`} className="rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
                              Incele
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tamamlanan incelemeler */}
          {completed.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-emerald-700">Tamamlanan Incelemeler ({completed.length})</h2>
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b bg-slate-50">
                    <tr>
                      <th className="p-3 font-medium text-slate-600">Inceleme</th>
                      <th className="p-3 font-medium text-slate-600">Gorev</th>
                      <th className="p-3 font-medium text-slate-600">Durum</th>
                      <th className="p-3 font-medium text-slate-600">Atanma</th>
                      <th className="p-3 font-medium text-slate-600">Detay</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {completed.map((r) => {
                      const si = STATUS_LABELS[r.status] ?? { label: r.status, cls: "bg-slate-100 text-slate-600" };
                      return (
                        <tr key={r.review_id} className="hover:bg-slate-50">
                          <td className="p-3 font-mono text-xs">{r.review_id.slice(0, 12)}</td>
                          <td className="p-3 font-mono text-xs">{r.mission_id.slice(0, 12)}</td>
                          <td className="p-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${si.cls}`}>{si.label}</span></td>
                          <td className="p-3 text-xs text-slate-500">{new Date(r.assigned_at).toLocaleString("tr-TR")}</td>
                          <td className="p-3">
                            <Link href={`/reviews/${r.review_id}`} className="text-xs text-sky-600 hover:underline">Gor</Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
