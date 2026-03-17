/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Farmer Subscriptions",
};

export default function FarmerSubscriptionsPage() {
  return (
    <section className="space-y-4" aria-label="Farmer subscriptions" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Abonelikler</h1>
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Henüz aktif aboneliğiniz yok.
      </div>
    </section>
  );
}
