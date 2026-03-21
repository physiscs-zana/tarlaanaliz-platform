/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: Pilot gorev listesi — API'den cekilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie, decodeJwtPayload } from "@/lib/api";

interface PilotMission {
  mission_id: string;
  field_id: string;
  status: string;
  mission_date: string;
  crop_type: string | null;
  analysis_type: string | null;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PLANNED: { label: "Planlandi", className: "bg-blue-100 text-blue-800" },
  ASSIGNED: { label: "Atandi", className: "bg-indigo-100 text-indigo-800" },
  ACKED: { label: "Kabul Edildi", className: "bg-cyan-100 text-cyan-800" },
  FLOWN: { label: "Ucus Tamamlandi", className: "bg-teal-100 text-teal-800" },
  UPLOADED: { label: "Yuklendi", className: "bg-violet-100 text-violet-800" },
  ANALYZING: { label: "Analiz Ediliyor", className: "bg-purple-100 text-purple-800" },
  DONE: { label: "Tamamlandi", className: "bg-emerald-100 text-emerald-800" },
  FAILED: { label: "Basarisiz", className: "bg-rose-100 text-rose-800" },
  CANCELLED: { label: "Iptal Edildi", className: "bg-slate-100 text-slate-600" },
};

export default function PilotMissionsPage() {
  const [missions, setMissions] = useState<PilotMission[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMissions = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/me/missions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Gorevler yuklenemedi");
      const data = (await res.json()) as PilotMission[];
      setMissions(data ?? []);
    } catch { setMissions([]); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchMissions(); }, [fetchMissions]);

  return (
    <section className="space-y-4" aria-label="Pilot missions">
      <h1 className="text-2xl font-semibold">Gorevlerim</h1>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : missions.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
          <p className="text-lg font-medium text-slate-500">Atanmis gorev bulunmamaktadir.</p>
          <p className="mt-1 text-sm text-slate-400">Gorev atamaniz yapildiginda burada gorunecektir.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {missions.map((m) => {
            const si = STATUS_LABELS[m.status] ?? { label: m.status, className: "bg-slate-100 text-slate-600" };
            return (
              <div key={m.mission_id} className="rounded-lg border border-slate-200 bg-white p-4 space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-900">Gorev #{m.mission_id.slice(0, 8)}</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${si.className}`}>{si.label}</span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span>Tarih: {m.mission_date}</span>
                  {m.crop_type && <span>Urun: {m.crop_type}</span>}
                  {m.analysis_type && <span>Analiz: {m.analysis_type}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
