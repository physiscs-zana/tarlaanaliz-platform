/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-083: Il Operatoru KPI + kapasite metrikleri. */
/* KR-066: PII GORMEZ — yalnizca FieldID/ozet KPI gorunur. */

export default function IlDashboardPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Il Operatoru Dashboard</h1>
      <p className="text-xs text-amber-600">
        KR-066: Bu ekranda kisisel veriler (PII) gosterilmez. Yalnizca ozet KPI ve kapasite metrikleri goruntulenir.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Toplam Tarla</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Aktif Gorev</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Tamamlanan Analiz</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
          <p className="text-3xl font-bold text-slate-800">—</p>
          <p className="mt-1 text-sm text-slate-500">Gelir Payi (TL)</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-medium mb-2">Kapasite Planlama</h2>
        <p className="text-sm text-slate-500">
          Pilot kapasite durumu ve gorev yogunlugu bu bolumde izlenir.
        </p>
      </div>
    </section>
  );
}
