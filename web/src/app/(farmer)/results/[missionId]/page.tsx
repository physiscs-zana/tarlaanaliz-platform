/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-025/KR-026: Sonuclar harita uzerinde renk + desen/ikon ile gosterilir. */
/* KR-018/KR-082: Graceful degradation — rapor seviyesi (Temel/Genisletilmis/Kapsamli). */
/* KR-084: Termal stres katmani (opsiyonel). */

import { cookies } from "next/headers";

import { COOKIE_TOKEN_KEY } from "@/lib/constants";
import { getResult } from "@/features/results/services/resultService";
import { LayerList } from "@/features/results/components/LayerList";
import { MapLayerViewer } from "@/features/results/components/MapLayerViewer";

const REPORT_TIER_LABELS: Record<string, string> = {
  TEMEL: "Temel Rapor (4 bant — NDVI, NDRE, stres göstergeleri)",
  GENISLETILMIS: "Genişletilmiş Rapor (5 bant — + EVI, chlorophyll, Sentinel-2 uyumlu)",
  KAPSAMLI: "Kapsamlı Rapor (5 bant + termal — + sulama stresi, CWSI)",
};

interface ResultPageProps {
  params: Promise<{ missionId: string }>;
}

export default async function ResultPage({ params }: ResultPageProps) {
  const { missionId } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_TOKEN_KEY)?.value;

  if (!token) return <p>Oturum bulunamadı.</p>;

  let result;
  try {
    result = await getResult(missionId, token);
  } catch {
    return <p className="text-red-600">Sonuçlar yüklenemedi.</p>;
  }

  const tierLabel = REPORT_TIER_LABELS[result.reportTier] ?? result.reportTier;

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Analiz Sonuçları</h1>
        {/* KR-026: Özet rapor (PDF) indirme */}
        <a
          href={`/api/results/${missionId}/pdf`}
          download
          className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
        >
          PDF İndir
        </a>
      </div>

      {/* KR-018/KR-082: Rapor seviyesi bilgilendirmesi */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-sm font-medium text-slate-700">Rapor Seviyesi: {tierLabel}</p>
        <p className="mt-1 text-xs text-slate-500">
          Bant sınıfı: {result.bandClass} | Güven skoru: {(result.confidenceScore * 100).toFixed(1)}%
        </p>
        {result.bandClass === "BASIC_4BAND" ? (
          <p className="mt-2 text-xs text-amber-600">
            Bu rapor 4 bantlı sensör verisiyle üretilmiştir. Blue bant mevcut olmadığından EVI, chlorophyll-a ve Sentinel-2 uyumlu indeksler üretilememiştir.
          </p>
        ) : null}
        {!result.thermalSummary ? (
          <p className="mt-1 text-xs text-amber-600">
            Termal bant mevcut olmadığından termal stres haritası bu raporda yer almamaktadır.
          </p>
        ) : null}
      </div>

      {/* KR-084: Termal ozet (opsiyonel) */}
      {result.thermalSummary ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h2 className="font-medium text-red-800">Termal Analiz Özeti</h2>
          <ul className="mt-2 space-y-1 text-sm text-red-700">
            <li>CWSI (Su Stresi): {result.thermalSummary.cwsi.toFixed(2)}</li>
            <li>Canopy Sıcaklık: {result.thermalSummary.canopyTemp.toFixed(1)} °C</li>
            <li>Canopy-Toprak Delta: {result.thermalSummary.canopySoilDeltaT.toFixed(1)} °C</li>
            <li>Sulama Etkinliği: {(result.thermalSummary.irrigationEfficiency * 100).toFixed(0)}%</li>
          </ul>
        </div>
      ) : null}

      {/* KR-064: Katman listesi + harita gorunumu */}
      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-2 font-medium">Katmanlar</h2>
          <LayerList layers={result.availableLayers} />
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <MapLayerViewer layers={result.availableLayers} />
        </div>
      </div>
    </section>
  );
}
