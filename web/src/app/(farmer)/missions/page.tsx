/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: Analiz listesi — API'den cekilir, veri yoksa bilgi mesaji gosterilir. */

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
interface Mission {
  mission_id: string;
  field_id: string;
  mission_date: string;
  status: string;
  crop_type: string | null;
  analysis_type: string | null;
  pilot_id: string | null;
  subscription_id: string | null;
}

/* ------- Constants ------- */
const PENDING_STATUSES = new Set(["PLANNED", "PAYMENT_PENDING"]);

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PLANNED: { label: "Odeme Bekleniyor", className: "bg-amber-100 text-amber-800" },
  ASSIGNED: { label: "Pilot Atandi", className: "bg-indigo-100 text-indigo-800" },
  ACCEPTED: { label: "Kabul Edildi", className: "bg-cyan-100 text-cyan-800" },
  ACKED: { label: "Kabul Edildi", className: "bg-cyan-100 text-cyan-800" },
  IN_PROGRESS: { label: "Ucus Devam Ediyor", className: "bg-amber-100 text-amber-800" },
  FLOWN: { label: "Ucus Tamamlandi", className: "bg-teal-100 text-teal-800" },
  COMPLETED: { label: "Tamamlandi", className: "bg-teal-100 text-teal-800" },
  UPLOADED: { label: "Yuklendi", className: "bg-violet-100 text-violet-800" },
  IN_ANALYSIS: { label: "Analiz Ediliyor", className: "bg-purple-100 text-purple-800" },
  ANALYZING: { label: "Analiz Ediliyor", className: "bg-purple-100 text-purple-800" },
  ANALYSIS_COMPLETED: { label: "Analiz Tamamlandi", className: "bg-blue-100 text-blue-800" },
  VERIFIED: { label: "Dogrulandi", className: "bg-emerald-100 text-emerald-800" },
  DELIVERED: { label: "Teslim Edildi", className: "bg-emerald-100 text-emerald-800" },
  DONE: { label: "Tamamlandi", className: "bg-emerald-100 text-emerald-800" },
  FAILED: { label: "Basarisiz", className: "bg-rose-100 text-rose-800" },
  CANCELLED: { label: "Iptal Edildi", className: "bg-slate-100 text-slate-600" },
  ON_HOLD: { label: "Beklemede", className: "bg-orange-100 text-orange-800" },
  REJECTED: { label: "Reddedildi", className: "bg-rose-100 text-rose-800" },
};

const CROP_LABELS: Record<string, string> = {
  PAMUK: "Pamuk",
  ANTEP_FISTIGI: "Antep Fistigi",
  MISIR: "Misir",
  BUGDAY: "Bugday",
  AYCICEGI: "Aycicegi",
  UZUM: "Uzum",
  ZEYTIN: "Zeytin",
  KIRMIZI_MERCIMEK: "Kirmizi Mercimek",
  COTTON: "Pamuk",
  WHEAT: "Bugday",
  CORN: "Misir",
};

const ANALYSIS_LABELS: Record<string, string> = {
  MULTISPECTRAL: "Multispektral",
  SEASONAL: "Sezonluk",
  THERMAL: "Termal",
  RGB: "RGB",
  FULL: "Tam Analiz",
};

/* ------- Mission Card ------- */
function MissionCard({ m }: { m: Mission }) {
  const statusInfo = STATUS_LABELS[m.status] ?? { label: m.status, className: "bg-slate-100 text-slate-600" };
  const cropLabel = m.crop_type ? (CROP_LABELS[m.crop_type] ?? m.crop_type) : null;
  const analysisLabel = m.analysis_type ? (ANALYSIS_LABELS[m.analysis_type] ?? m.analysis_type) : null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-slate-900">Analiz #{m.mission_id.slice(0, 8)}</p>
          {m.subscription_id && (
            <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-600">Sezonluk</span>
          )}
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusInfo.className}`}>
          {statusInfo.label}
        </span>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>Tarih: {m.mission_date}</span>
        {cropLabel && <span>Urun: {cropLabel}</span>}
        {analysisLabel && <span>Analiz: {analysisLabel}</span>}
      </div>
    </div>
  );
}

/* ------- Page ------- */
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

  const { approved, pending } = useMemo(() => {
    const pend: Mission[] = [];
    const appr: Mission[] = [];
    for (const m of missions) {
      if (PENDING_STATUSES.has(m.status)) {
        pend.push(m);
      } else {
        appr.push(m);
      }
    }
    return { pending: pend, approved: appr };
  }, [missions]);

  return (
    <section className="space-y-6">
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
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Sol Kolon: Onaylanan Analizler */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-emerald-700 border-b border-emerald-200 pb-2">
              Onaylanan Analizler ({approved.length})
            </h2>
            {approved.length > 0 ? (
              approved.map((m) => <MissionCard key={m.mission_id} m={m} />)
            ) : (
              <div className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 py-8 text-center">
                <p className="text-sm text-slate-400">Henuz onaylanan analiz bulunmamaktadir.</p>
              </div>
            )}
          </div>

          {/* Sag Kolon: Bekleyen Analiz Talepleri */}
          <div className="space-y-3">
            <h2 className="text-sm font-semibold text-amber-700 border-b border-amber-200 pb-2">
              Bekleyen Analiz Talepleri ({pending.length})
            </h2>
            {pending.length > 0 ? (
              pending.map((m) => <MissionCard key={m.mission_id} m={m} />)
            ) : (
              <div className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 py-8 text-center">
                <p className="text-sm text-slate-400">Bekleyen analiz talebi bulunmamaktadir.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
