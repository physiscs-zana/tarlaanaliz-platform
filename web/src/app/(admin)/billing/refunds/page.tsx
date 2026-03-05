/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Iade (REFUNDED) — yalnizca PAID iken CENTRAL_ADMIN aksiyonu ile yapilir. */

export default function BillingRefundsPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Iade Islemleri</h1>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <p className="text-sm text-slate-600">
          Iade yalnizca PAID durumundaki odemeler icin CENTRAL_ADMIN onayi ile yapilabilir.
        </p>
        <p className="text-sm text-slate-500">Aktif iade talebi bulunmuyor.</p>
      </div>
    </section>
  );
}
