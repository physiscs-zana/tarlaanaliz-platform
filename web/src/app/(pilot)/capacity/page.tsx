/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: kapasite/çalışma günü kısıtları. */

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Pilot Capacity" };

export default function PilotCapacityPage() {
  return (
    <section className="space-y-4" aria-label="Pilot capacity" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Kapasite Ayarları</h1>
      <ul className="list-inside list-disc rounded-lg border border-slate-200 bg-white p-4 text-sm">
        <li>Çalışma günleri: en fazla 6 gün/hafta</li>
        <li>Günlük kapasite: 2750 dönüm/gün (varsayılan, aralık: 2500–3000)</li>
        <li>Kapasite aşım toleransı: yalnızca acil durumda %10 (maks. 3300 dönüm)</li>
      </ul>
    </section>
  );
}
