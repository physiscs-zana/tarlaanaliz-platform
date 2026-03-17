/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Expert onboarding, atama ve performans yonetimi. */
/* KR-064: Uzmanlik alanlari — DISEASE, PEST, WEED, WATER_STRESS, N_STRESS, THERMAL_STRESS */

"use client";

import { useState } from "react";
import type { Metadata } from "next";

/* ------- Types ------- */
interface Expert {
  id: string;
  name: string;
  phone: string;
  specialization: Specialization;
  reviewCount: number;
  slaRate: string;
  status: "Aktif" | "Onay Bekliyor" | "Pasif";
}

type Specialization =
  | "Bitki Hastaliklari"
  | "Zararli Bocek"
  | "Yabanci Ot"
  | "Su Stresi"
  | "Azot / Gubre"
  | "Termal Stres"
  | "Genel";

const SPECIALIZATIONS: Specialization[] = [
  "Bitki Hastaliklari",
  "Zararli Bocek",
  "Yabanci Ot",
  "Su Stresi",
  "Azot / Gubre",
  "Termal Stres",
  "Genel",
];

const SPEC_COLORS: Record<Specialization, string> = {
  "Bitki Hastaliklari": "bg-rose-50 text-rose-700 border-rose-200",
  "Zararli Bocek": "bg-orange-50 text-orange-700 border-orange-200",
  "Yabanci Ot": "bg-lime-50 text-lime-700 border-lime-200",
  "Su Stresi": "bg-blue-50 text-blue-700 border-blue-200",
  "Azot / Gubre": "bg-violet-50 text-violet-700 border-violet-200",
  "Termal Stres": "bg-red-50 text-red-700 border-red-200",
  Genel: "bg-slate-50 text-slate-700 border-slate-200",
};

/* ------- Initial mock data ------- */
const INITIAL_EXPERTS: Expert[] = [
  { id: "e1", name: "Dr. Ayse K.", phone: "0532***4567", specialization: "Bitki Hastaliklari", reviewCount: 142, slaRate: "%98", status: "Aktif" },
  { id: "e2", name: "Mehmet T.", phone: "0541***8901", specialization: "Zararli Bocek", reviewCount: 89, slaRate: "%95", status: "Aktif" },
  { id: "e3", name: "Fatma S.", phone: "0505***2345", specialization: "Yabanci Ot", reviewCount: 67, slaRate: "%97", status: "Aktif" },
  { id: "e4", name: "Ali R.", phone: "0544***6789", specialization: "Su Stresi", reviewCount: 34, slaRate: "%92", status: "Onay Bekliyor" },
  { id: "e5", name: "Zeynep D.", phone: "0533***1122", specialization: "Azot / Gubre", reviewCount: 51, slaRate: "%96", status: "Aktif" },
  { id: "e6", name: "Hasan B.", phone: "0542***3344", specialization: "Bitki Hastaliklari", reviewCount: 23, slaRate: "%94", status: "Aktif" },
  { id: "e7", name: "Elif M.", phone: "0506***5566", specialization: "Zararli Bocek", reviewCount: 12, slaRate: "—", status: "Onay Bekliyor" },
];

/* ------- Status badge ------- */
function StatusBadge({ status }: { status: Expert["status"] }) {
  const cls =
    status === "Aktif"
      ? "bg-emerald-50 text-emerald-700"
      : status === "Onay Bekliyor"
        ? "bg-amber-50 text-amber-700"
        : "bg-slate-100 text-slate-500";
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>;
}

/* ------- Main page ------- */
export default function ExpertManagementPage() {
  const [experts, setExperts] = useState<Expert[]>(INITIAL_EXPERTS);
  const [filterSpec, setFilterSpec] = useState<Specialization | "Tumu">("Tumu");
  const [showAddForm, setShowAddForm] = useState(false);

  /* Add form state */
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newSpec, setNewSpec] = useState<Specialization>("Genel");

  const filtered = filterSpec === "Tumu" ? experts : experts.filter((e) => e.specialization === filterSpec);

  /* Group by specialization */
  const grouped = SPECIALIZATIONS.reduce<Record<Specialization, Expert[]>>((acc, spec) => {
    const items = filtered.filter((e) => e.specialization === spec);
    if (items.length > 0) acc[spec] = items;
    return acc;
  }, {} as Record<Specialization, Expert[]>);

  const handleAdd = () => {
    if (!newName.trim() || !newPhone.trim()) return;
    const expert: Expert = {
      id: `e-${Date.now()}`,
      name: newName.trim(),
      phone: newPhone.trim(),
      specialization: newSpec,
      reviewCount: 0,
      slaRate: "—",
      status: "Onay Bekliyor",
    };
    setExperts((prev) => [...prev, expert]);
    setNewName("");
    setNewPhone("");
    setNewSpec("Genel");
    setShowAddForm(false);
  };

  const handleDelete = (id: string) => {
    setExperts((prev) => prev.filter((e) => e.id !== id));
  };

  const handleApprove = (id: string) => {
    setExperts((prev) => prev.map((e) => (e.id === id ? { ...e, status: "Aktif" as const } : e)));
  };

  const activeCount = experts.filter((e) => e.status === "Aktif").length;
  const pendingCount = experts.filter((e) => e.status === "Onay Bekliyor").length;

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Uzman Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            {activeCount} aktif · {pendingCount} onay bekliyor · {experts.length} toplam
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          {showAddForm ? "Iptal" : "Uzman Ekle"}
        </button>
      </div>

      {/* Add form */}
      {showAddForm && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Yeni Uzman Ekle</h2>
          <div className="grid gap-3 sm:grid-cols-4">
            <input
              placeholder="Ad Soyad"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              placeholder="Telefon"
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={newSpec}
              onChange={(e) => setNewSpec(e.target.value as Specialization)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            >
              {SPECIALIZATIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={handleAdd}
              disabled={!newName.trim() || !newPhone.trim()}
              className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Ekle
            </button>
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setFilterSpec("Tumu")}
          className={`rounded-full border px-3 py-1 text-xs font-medium transition ${filterSpec === "Tumu" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}
        >
          Tumu ({experts.length})
        </button>
        {SPECIALIZATIONS.map((spec) => {
          const count = experts.filter((e) => e.specialization === spec).length;
          if (count === 0) return null;
          return (
            <button
              key={spec}
              onClick={() => setFilterSpec(spec)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition ${filterSpec === spec ? "border-slate-900 bg-slate-900 text-white" : `border ${SPEC_COLORS[spec]}`}`}
            >
              {spec} ({count})
            </button>
          );
        })}
      </div>

      {/* Grouped expert cards */}
      {Object.entries(grouped).map(([spec, items]) => (
        <div key={spec}>
          <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <span className={`inline-block rounded-full border px-2.5 py-0.5 text-xs ${SPEC_COLORS[spec as Specialization]}`}>
              {spec}
            </span>
            <span className="text-slate-400">({items.length})</span>
          </h2>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-100 bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-slate-600">Ad Soyad</th>
                  <th className="px-4 py-2 text-left font-medium text-slate-600">Telefon</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Inceleme</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">SLA</th>
                  <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Islem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {items.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-medium text-slate-900">{e.name}</td>
                    <td className="px-4 py-2.5 text-slate-500">{e.phone}</td>
                    <td className="px-4 py-2.5 text-right text-slate-600">{e.reviewCount}</td>
                    <td className="px-4 py-2.5 text-right text-slate-600">{e.slaRate}</td>
                    <td className="px-4 py-2.5"><StatusBadge status={e.status} /></td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {e.status === "Onay Bekliyor" && (
                          <button onClick={() => handleApprove(e.id)} className="rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
                            Onayla
                          </button>
                        )}
                        <button onClick={() => handleDelete(e.id)} className="rounded bg-rose-50 px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-100">
                          Sil
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          Bu kategoride uzman bulunmuyor.
        </div>
      )}
    </section>
  );
}
