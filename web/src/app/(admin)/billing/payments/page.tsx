/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: BILLING_ADMIN IBAN dekont onayi. */
/* KR-033 §10: T+1 SLA — bir sonraki is gunu 17:00'e kadar onay zorunlu. */

export default function BillingPaymentsPage() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Odeme Yonetimi (BILLING_ADMIN)</h1>

      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
        KR-033 §10: Dekont yuklendikten sonra T+1 (bir sonraki is gunu 17:00) onay SLA&apos;si vardir.
        SLA ihlalinde CENTRAL_ADMIN&apos;e otomatik uyari gonderilir.
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Bekleyen Dekontlar</h2>
        <p className="text-sm text-slate-500">Bekleyen dekont bulunmuyor.</p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Eskalasyon Kurallari</h2>
        <ul className="text-sm text-slate-600 space-y-1 list-disc pl-4">
          <li>500 TL ve alti: BILLING_ADMIN tek imzayla onaylayabilir.</li>
          <li>500 TL ustu: CENTRAL_ADMIN ikinci onayi zorunludur.</li>
          <li>Supheli makbuz: CENTRAL_ADMIN&apos;e eskalasyon zorunlu.</li>
        </ul>
      </div>
    </section>
  );
}
