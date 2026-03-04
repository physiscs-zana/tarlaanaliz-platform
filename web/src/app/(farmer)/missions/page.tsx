/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Farmer Missions",
};

export default function FarmerMissionsPage() {
  return (
    <section className="space-y-4" aria-label="Farmer missions" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Görevler</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
        <p>Mission #msn_1001 · planlandı</p>
      </div>
    </section>
  );
}
