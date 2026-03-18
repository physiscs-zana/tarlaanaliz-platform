/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-017: Analiz sonuclari — API'den cekilir, veri yoksa bilgi mesaji gosterilir. */
/* KR-018: Kalibrasyonsuz analiz ciktisi listelenmez. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface ResultLayer {
  layer_name: string;
  layer_type: string;
  uri: string;
}

interface ResultSummary {
  analysis_job_id: string;
  mission_id: string;
  layers: ResultLayer[];
  quality_status: string;
  report_tier: string;
  band_class: string;
  available_indices: string[];
}

const TIER_LABELS: Record<string, { label: string; className: string }> = {
  TEMEL: { label: "Temel Rapor", className: "bg-slate-100 text-slate-700" },
  GENISLETILMIS: { label: "Genisletilmis Rapor", className: "bg-blue-100 text-blue-700" },
  KAPSAMLI: { label: "Kapsamli Rapor", className: "bg-emerald-100 text-emerald-700" },
};

export default function FarmerResultsPage() {
  const router = useRouter();
  const [results, setResults] = useState<ResultSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
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
      const res = await fetch(`${baseUrl}/results`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { router.push("/login"); return; }
      if (!res.ok) throw new Error("Sonuclar yuklenemedi");
      const data = (await res.json()) as ResultSummary[];
      setResults(data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => { fetchResults(); }, [fetchResults]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Sonuclar</h1>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : results.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ VERI-BILGI BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Analiz tamamlandiginda sonuclariniz burada goruntulenecektir.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {results.map((r) => {
            const tierInfo = TIER_LABELS[r.report_tier] ?? { label: r.report_tier, className: "bg-slate-100 text-slate-600" };
            return (
              <a
                key={r.analysis_job_id}
                href={`/results/${r.mission_id}`}
                className="block rounded-lg border border-slate-200 bg-white p-4 hover:shadow-sm transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Gorev #{r.mission_id.slice(0, 8)}</p>
                    <p className="text-xs text-slate-500">
                      {r.layers.length} katman | {r.available_indices.join(", ")}
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${tierInfo.className}`}>
                    {tierInfo.label}
                  </span>
                </div>
              </a>
            );
          })}
        </div>
      )}
    </section>
  );
}
