/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-083: Il Operatoru operasyon metrikleri — PII gormeden KPI izleme. */
/* KR-066: PII GORMEZ. */

export default function IlMetricsPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Operasyon Metrikleri</h1>
      <p className="text-xs text-amber-600">
        KR-066: Bu ekranda kisisel veriler (PII) gosterilmez.
      </p>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Haftalik Ozet</h2>
        <div className="grid gap-3 sm:grid-cols-3 text-sm">
          <div>
            <p className="text-slate-500">Yeni Tarla Kaydi</p>
            <p className="text-xl font-bold">—</p>
          </div>
          <div>
            <p className="text-slate-500">Tamamlanan Ucus</p>
            <p className="text-xl font-bold">—</p>
          </div>
          <div>
            <p className="text-slate-500">Teslim Edilen Rapor</p>
            <p className="text-xl font-bold">—</p>
          </div>
        </div>
      </div>
    </section>
  );
}
