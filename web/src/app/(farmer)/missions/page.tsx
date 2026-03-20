/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: Analiz listesi — API'den cekilir, veri yoksa bilgi mesaji gosterilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface Mission {
  mission_id: string;
  field_id: string;
  mission_date: string;
  status: string;
  crop_type: string | null;
  analysis_type: string | null;
  pilot_id: string | null;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PLANNED: { label: "Planlandi", className: "bg-blue-100 text-blue-800" },
  ASSIGNED: { label: "Atandi", className: "bg-indigo-100 text-indigo-800" },
  ACKED: { label: "Kabul Edildi", className: "bg-cyan-100 text-cyan-800" },
  IN_PROGRESS: { label: "Devam Ediyor", className: "bg-amber-100 text-amber-800" },
  FLOWN: { label: "Ucus Tamamlandi", className: "bg-teal-100 text-teal-800" },
  UPLOADED: { label: "Yuklendi", className: "bg-violet-100 text-violet-800" },
  ANALYZING: { label: "Analiz Ediliyor", className: "bg-purple-100 text-purple-800" },
  DONE: { label: "Tamamlandi", className: "bg-emerald-100 text-emerald-800" },
  COMPLETED: { label: "Tamamlandi", className: "bg-emerald-100 text-emerald-800" },
  FAILED: { label: "Basarisiz", className: "bg-rose-100 text-rose-800" },
  CANCELLED: { label: "Iptal Edildi", className: "bg-slate-100 text-slate-600" },
};

const CROP_LABELS: Record<string, string> = {
  PAMUK: "Pamuk",
  BUGDAY: "Bugday",
  MISIR: "Misir",
  COTTON: "Pamuk",
  WHEAT: "Bugday",
  CORN: "Misir",
};

const ANALYSIS_LABELS: Record<string, string> = {
  MULTISPECTRAL: "Multispektral",
  THERMAL: "Termal",
  RGB: "RGB",
};

export default function FarmerMissionsPage() {
  const router = useRouter();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMissions = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) {
      setError("Oturum bulunamadi. Lutfen tekrar giris yapin.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/missions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { router.push("/login"); return; }
      if (!res.ok) throw new Error("Analizler yuklenemedi");
      const data = (await res.json()) as Mission[];
      setMissions(data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => { fetchMissions(); }, [fetchMissions]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Analizlerim</h1>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : missions.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ ANALIZ TALEBI BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Tarlaniz icin analiz talebi olusturdugunuzda burada listelenecektir.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {missions.map((m) => {
            const statusInfo = STATUS_LABELS[m.status] ?? { label: m.status, className: "bg-slate-100 text-slate-600" };
            const cropLabel = m.crop_type ? (CROP_LABELS[m.crop_type] ?? m.crop_type) : null;
            const analysisLabel = m.analysis_type ? (ANALYSIS_LABELS[m.analysis_type] ?? m.analysis_type) : null;
            return (
              <div key={m.mission_id} className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-900">Analiz #{m.mission_id.slice(0, 8)}</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusInfo.className}`}>
                    {statusInfo.label}
                  </span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span>Tarih: {m.mission_date}</span>
                  {cropLabel && <span>Urun: {cropLabel}</span>}
                  {analysisLabel && <span>Analiz Tipi: {analysisLabel}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
