/* BOUND: TARLAANALIZ_SSOT_v1_1_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: planlama kapasite sınırları ile uyumlu görünürlük. */

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Pilot Planner" };

export default function PilotPlannerPage() {
  return (
    <section className="space-y-4" aria-label="Pilot planner" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Planlayıcı</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
        Haftalık plan görünümü (stub) · work_days ≤ 6 kuralına göre backend doğrulaması bekleniyor.
      </div>
    </section>
  );
}
