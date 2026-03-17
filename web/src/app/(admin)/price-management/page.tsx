/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Fiyat yonetimi — plan olusturma, guncelleme, yayinlama. */

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Fiyat Yonetimi" };

const plans = [
  { name: "Sezonluk Temel", perHa: "120 TL", minArea: "5 ha", interval: "14 gun", status: "Yayinda" },
  { name: "Sezonluk Pro", perHa: "180 TL", minArea: "2 ha", interval: "7 gun", status: "Yayinda" },
  { name: "Tek Sefer", perHa: "250 TL", minArea: "1 ha", interval: "—", status: "Yayinda" },
  { name: "Kooperatif Ozel", perHa: "95 TL", minArea: "50 ha", interval: "14 gun", status: "Taslak" },
] as const;

export default function PriceManagementPage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Fiyat Yonetimi</h1>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Plan</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Hektar Basina</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Min. Alan</th>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Tarama Sikligi</th>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Durum</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {plans.map((p) => (
              <tr key={p.name} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{p.name}</td>
                <td className="px-4 py-3 text-right text-slate-600">{p.perHa}</td>
                <td className="px-4 py-3 text-right text-slate-600">{p.minArea}</td>
                <td className="px-4 py-3 text-slate-600">{p.interval}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${p.status === "Yayinda" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                    {p.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400">
        Fiyat degisiklikleri sadece CENTRAL_ADMIN tarafindan yayinlanabilir. Taslak planlar otomatik olarak audit log&apos;a kaydedilir.
      </p>
    </section>
  );
}
