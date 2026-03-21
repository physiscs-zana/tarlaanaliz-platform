/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Uzman inceleme kuyrugu — API'den cekilir, gorev yoksa bos durum gosterilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
interface QueueItem {
  review_id: string;
  mission_id: string;
  analysis_result_id: string;
  status: string;
  assigned_at: string;
  priority: number;
}

interface ExpertStats {
  total_completed: number;
  pending_count: number;
  in_progress_count: number;
  completed_today: number;
  avg_completion_minutes: number | null;
}

/* ------- Stat Card ------- */
function StatCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accent ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}

/* ------- Page ------- */
export default function ExpertQueuePage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [stats, setStats] = useState<ExpertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [queueRes, statsRes] = await Promise.all([
        fetch(`${baseUrl}/expert-portal/reviews/queue`, { headers }),
        fetch(`${baseUrl}/expert-portal/my-stats`, { headers }),
      ]);

      if (queueRes.ok) {
        const data = (await queueRes.json()) as QueueItem[];
        setItems(data ?? []);
      }

      if (statsRes.ok) {
        const data = (await statsRes.json()) as ExpertStats;
        setStats(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const STATUS_LABELS: Record<string, { label: string; className: string }> = {
    PENDING: { label: "Bekliyor", className: "bg-amber-100 text-amber-800" },
    IN_PROGRESS: { label: "Inceleniyor", className: "bg-blue-100 text-blue-800" },
  };

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Inceleme Kuyrugu</h1>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Toplam Tamamlanan" value={stats.total_completed.toLocaleString("tr-TR")} accent="text-emerald-700" />
          <StatCard label="Bugun Tamamlanan" value={stats.completed_today.toLocaleString("tr-TR")} />
          <StatCard label="Bekleyen" value={stats.pending_count.toLocaleString("tr-TR")} accent="text-amber-700" />
          <StatCard
            label="Ort. Sure"
            value={stats.avg_completion_minutes !== null ? `${stats.avg_completion_minutes} dk` : "\u2014"}
          />
        </div>
      )}

      {/* Queue */}
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
                <th className="p-3 font-medium text-slate-600">Inceleme</th>
                <th className="p-3 font-medium text-slate-600">Gorev</th>
                <th className="p-3 font-medium text-slate-600">Durum</th>
                <th className="p-3 font-medium text-slate-600">Atanma</th>
                <th className="p-3 font-medium text-slate-600">Aksiyon</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {items.map((item) => {
                const statusInfo = STATUS_LABELS[item.status] ?? { label: item.status, className: "bg-slate-100 text-slate-600" };
                return (
                  <tr key={item.review_id} className="hover:bg-slate-50">
                    <td className="p-3 font-mono text-xs">{item.review_id.slice(0, 12)}</td>
                    <td className="p-3 font-mono text-xs">{item.mission_id.slice(0, 12)}</td>
                    <td className="p-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusInfo.className}`}>{statusInfo.label}</span>
                    </td>
                    <td className="p-3 text-xs text-slate-500">{item.assigned_at ? new Date(item.assigned_at).toLocaleString("tr-TR") : "\u2014"}</td>
                    <td className="p-3">
                      <Link href={`/review/${item.review_id}`} className="rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
                        Incele
                      </Link>
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
