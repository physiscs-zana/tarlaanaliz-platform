/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Expert onboarding, atama ve performans yonetimi. */

import type { Metadata } from "next";

export const metadata: Metadata = { title: "Expert Yonetimi" };

const experts = [
  { name: "Dr. Ayse K.", specialization: "Bitki Hastaliklari", reviewCount: 142, slaRate: "%98", status: "Aktif" },
  { name: "Mehmet T.", specialization: "Zararli Bocek", reviewCount: 89, slaRate: "%95", status: "Aktif" },
  { name: "Fatma S.", specialization: "Yabanci Ot", reviewCount: 67, slaRate: "%97", status: "Aktif" },
  { name: "Ali R.", specialization: "Su Stresi", reviewCount: 34, slaRate: "%92", status: "Onay Bekliyor" },
] as const;

export default function ExpertManagementPage() {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Expert Yonetimi</h1>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {experts.length} expert
        </span>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Expert</th>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Uzmanlik</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Inceleme</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">SLA</th>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Durum</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {experts.map((e) => (
              <tr key={e.name} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{e.name}</td>
                <td className="px-4 py-3 text-slate-600">{e.specialization}</td>
                <td className="px-4 py-3 text-right text-slate-600">{e.reviewCount}</td>
                <td className="px-4 py-3 text-right text-slate-600">{e.slaRate}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${e.status === "Aktif" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                    {e.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
