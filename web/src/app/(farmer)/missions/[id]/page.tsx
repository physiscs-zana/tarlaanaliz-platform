/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-018: Ciftci rapor seviyesini ve uretilebilen/uretilemeyen katmanlari gormeli. */
/* KR-002: Harita katman renk/desen bilgileri layer registry'den cekilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface MissionDetail {
  mission_id: string;
  field_id: string;
  mission_date: string;
  status: string;
  crop_type: string | null;
  analysis_type: string | null;
  pilot_id: string | null;
  subscription_id: string | null;
}

interface LayerInfo {
  code: string;
  name_tr: string;
  color: string;
  pattern: string;
  requires_bands: string[];
}

const STATUS_LABELS: Record<string, string> = {
  PLANNED: "Odeme Bekleniyor",
  ASSIGNED: "Pilot Atandi",
  ACCEPTED: "Kabul Edildi",
  IN_PROGRESS: "Ucus Devam Ediyor",
  COMPLETED: "Tamamlandi",
  UPLOADED: "Yuklendi",
  IN_ANALYSIS: "Analiz Ediliyor",
  ANALYSIS_COMPLETED: "Analiz Tamamlandi",
  VERIFIED: "Dogrulandi",
  DELIVERED: "Teslim Edildi",
  FAILED: "Basarisiz",
  CANCELLED: "Iptal Edildi",
};

/* KR-018: Bant kapasite seviyeleri */
const BAND_TIERS = [
  {
    tier: "BASIC_4BAND",
    label: "Temel Saglik Raporu",
    description: "NDVI, NDRE, stres gostergeleri, hastalik/zararli/yabanci ot tespiti",
    bands: ["Green", "Red", "RedEdge", "NIR"],
  },
  {
    tier: "EXTENDED_5BAND",
    label: "Genisletilmis Rapor",
    description: "+ EVI, klorofil detay, Sentinel-2 uyumlu indeksler",
    bands: ["Blue", "Green", "Red", "RedEdge", "NIR"],
  },
  {
    tier: "THERMAL",
    label: "Kapsamli Rapor",
    description: "+ Termal stres haritasi, sulama optimizasyonu",
    bands: ["LWIR"],
  },
];

export default function MissionDetailPage() {
  const params = useParams();
  const missionId = params?.id as string;
  const [mission, setMission] = useState<MissionDetail | null>(null);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [missionsRes, layersRes] = await Promise.all([
        fetch(`${baseUrl}/missions`, { headers }),
        fetch(`${baseUrl}/layers`),
      ]);
      if (missionsRes.ok) {
        const data = (await missionsRes.json()) as MissionDetail[];
        const found = data.find((m) => m.mission_id === missionId);
        setMission(found ?? null);
      }
      if (layersRes.ok) {
        const data = (await layersRes.json()) as { layers: LayerInfo[] };
        setLayers(data.layers ?? []);
      }
    } catch { /* noop */ }
    setLoading(false);
  }, [missionId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;
  if (!mission) return <div className="py-12 text-center text-sm text-slate-500">Analiz bulunamadi.</div>;

  /* KR-018: Simdilik tum ciftciler 4 bant (DJI Mavic 3M) ile baslayacak.
     Bant bilgisi dataset'ten gelecek; su an varsayilan BASIC_4BAND. */
  const availableBands = new Set(["Green", "Red", "RedEdge", "NIR"]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Analiz Detayi</h1>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-mono text-slate-600">#{mission.mission_id.slice(0, 8)}</span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium">
            {STATUS_LABELS[mission.status] ?? mission.status}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><span className="text-slate-500">Tarih:</span> {mission.mission_date}</div>
          <div><span className="text-slate-500">Bitki:</span> {mission.crop_type ?? "—"}</div>
          <div><span className="text-slate-500">Analiz:</span> {mission.analysis_type ?? "—"}</div>
          {mission.subscription_id && <div><span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-600">Sezonluk Paket</span></div>}
        </div>
      </div>

      {/* KR-018: Rapor seviyesi ve katman bilgisi */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Rapor Katmanlari (KR-018)</h2>
        <p className="text-xs text-slate-500">
          Rapor seviyesi drone sensoru bant kapasitesine gore belirlenir. Eksik bantlar nedeniyle uretilemeyecek katmanlar isaretlenir.
        </p>

        {/* Bant kapasite seviyeleri */}
        <div className="space-y-2">
          {BAND_TIERS.map((tier) => {
            const supported = tier.bands.every((b) => availableBands.has(b));
            return (
              <div key={tier.tier} className={`rounded border p-2 text-sm ${supported ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50 opacity-60"}`}>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold ${supported ? "text-emerald-700" : "text-slate-400"}`}>
                    {supported ? "AKTIF" : "PASIF"}
                  </span>
                  <span className="font-medium">{tier.label}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{tier.description}</p>
              </div>
            );
          })}
        </div>

        {/* Katman listesi */}
        <div className="space-y-1">
          <h3 className="text-sm font-medium text-slate-700 mt-2">Harita Katmanlari</h3>
          {layers.map((layer) => {
            const canProduce = layer.requires_bands.every((b) => availableBands.has(b));
            return (
              <div key={layer.code} className="flex items-center gap-2 text-sm">
                <span className="w-3 h-3 rounded-full border" style={{ backgroundColor: layer.color }} />
                <span className={canProduce ? "text-slate-800" : "text-slate-400 line-through"}>{layer.name_tr}</span>
                {!canProduce && <span className="text-[10px] text-amber-600">(eksik bant)</span>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
