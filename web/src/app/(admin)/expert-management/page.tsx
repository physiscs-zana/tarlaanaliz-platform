/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Expert onboarding, atama ve performans yonetimi. */
/* KR-064: Analiz katmanlari — DISEASE, PEST, WEED, WATER_STRESS, N_STRESS, THERMAL_STRESS */
/* CropType VO: PAMUK, ANTEP_FISTIGI, MISIR, BUGDAY, AYCICEGI, UZUM, ZEYTIN, KIRMIZI_MERCIMEK */

"use client";

import { useState } from "react";

/* ------- Canonical lists (SSOT) ------- */

/** KR-064: Analiz katmanlari */
const ANALYSIS_LAYERS = [
  { code: "DISEASE", label: "Bitki Hastaligi" },
  { code: "PEST", label: "Zararli Bocek" },
  { code: "WEED", label: "Yabanci Ot" },
  { code: "WATER_STRESS", label: "Su Stresi" },
  { code: "N_STRESS", label: "Azot / Gubre" },
  { code: "THERMAL_STRESS", label: "Termal Stres" },
] as const;

/** CropType VO: SSOT kanonik bitki turleri */
const CROP_TYPES = [
  { code: "PAMUK", label: "Pamuk" },
  { code: "ANTEP_FISTIGI", label: "Antep Fistigi" },
  { code: "MISIR", label: "Misir" },
  { code: "BUGDAY", label: "Bugday" },
  { code: "AYCICEGI", label: "Aycicegi" },
  { code: "UZUM", label: "Uzum" },
  { code: "ZEYTIN", label: "Zeytin" },
  { code: "KIRMIZI_MERCIMEK", label: "Kirmizi Mercimek" },
] as const;

type LayerCode = (typeof ANALYSIS_LAYERS)[number]["code"];
type CropCode = (typeof CROP_TYPES)[number]["code"];

/** Uzmanin yetkin oldugu alan: bitki turu x analiz katmani */
interface Competency {
  crop: CropCode;
  layer: LayerCode;
}

interface Expert {
  id: string;
  name: string;
  phone: string;
  competencies: Competency[];
  reviewCount: number;
  slaRate: string;
  status: "Aktif" | "Onay Bekliyor" | "Pasif";
}

/* ------- Helpers ------- */
const cropLabel = (code: CropCode) => CROP_TYPES.find((c) => c.code === code)?.label ?? code;
const layerLabel = (code: LayerCode) => ANALYSIS_LAYERS.find((l) => l.code === code)?.label ?? code;

const LAYER_COLORS: Record<LayerCode, string> = {
  DISEASE: "bg-rose-50 text-rose-700 border-rose-200",
  PEST: "bg-orange-50 text-orange-700 border-orange-200",
  WEED: "bg-lime-50 text-lime-700 border-lime-200",
  WATER_STRESS: "bg-blue-50 text-blue-700 border-blue-200",
  N_STRESS: "bg-violet-50 text-violet-700 border-violet-200",
  THERMAL_STRESS: "bg-red-50 text-red-700 border-red-200",
};

const CROP_COLORS: Record<CropCode, string> = {
  PAMUK: "bg-sky-50 text-sky-700",
  ANTEP_FISTIGI: "bg-emerald-50 text-emerald-700",
  MISIR: "bg-yellow-50 text-yellow-700",
  BUGDAY: "bg-amber-50 text-amber-700",
  AYCICEGI: "bg-orange-50 text-orange-700",
  UZUM: "bg-purple-50 text-purple-700",
  ZEYTIN: "bg-green-50 text-green-700",
  KIRMIZI_MERCIMEK: "bg-red-50 text-red-700",
};

/* ------- Mock data ------- */
const INITIAL_EXPERTS: Expert[] = [
  {
    id: "e1", name: "Dr. Ayse K.", phone: "0532***4567", reviewCount: 142, slaRate: "%98", status: "Aktif",
    competencies: [
      { crop: "PAMUK", layer: "DISEASE" },
      { crop: "PAMUK", layer: "PEST" },
      { crop: "MISIR", layer: "DISEASE" },
    ],
  },
  {
    id: "e2", name: "Mehmet T.", phone: "0541***8901", reviewCount: 89, slaRate: "%95", status: "Aktif",
    competencies: [
      { crop: "BUGDAY", layer: "PEST" },
      { crop: "BUGDAY", layer: "WEED" },
      { crop: "AYCICEGI", layer: "PEST" },
    ],
  },
  {
    id: "e3", name: "Fatma S.", phone: "0505***2345", reviewCount: 67, slaRate: "%97", status: "Aktif",
    competencies: [
      { crop: "PAMUK", layer: "WEED" },
      { crop: "MISIR", layer: "WEED" },
      { crop: "AYCICEGI", layer: "WEED" },
      { crop: "BUGDAY", layer: "WEED" },
    ],
  },
  {
    id: "e4", name: "Ali R.", phone: "0544***6789", reviewCount: 34, slaRate: "%92", status: "Onay Bekliyor",
    competencies: [
      { crop: "PAMUK", layer: "WATER_STRESS" },
      { crop: "MISIR", layer: "WATER_STRESS" },
    ],
  },
  {
    id: "e5", name: "Zeynep D.", phone: "0533***1122", reviewCount: 51, slaRate: "%96", status: "Aktif",
    competencies: [
      { crop: "BUGDAY", layer: "N_STRESS" },
      { crop: "MISIR", layer: "N_STRESS" },
      { crop: "PAMUK", layer: "N_STRESS" },
    ],
  },
  {
    id: "e6", name: "Hasan B.", phone: "0542***3344", reviewCount: 23, slaRate: "%94", status: "Aktif",
    competencies: [
      { crop: "ZEYTIN", layer: "DISEASE" },
      { crop: "UZUM", layer: "DISEASE" },
      { crop: "ANTEP_FISTIGI", layer: "PEST" },
    ],
  },
];

/* ------- Components ------- */
function StatusBadge({ status }: { status: Expert["status"] }) {
  const cls =
    status === "Aktif" ? "bg-emerald-50 text-emerald-700"
    : status === "Onay Bekliyor" ? "bg-amber-50 text-amber-700"
    : "bg-slate-100 text-slate-500";
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>;
}

function CompetencyTags({ competencies }: { competencies: Competency[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {competencies.map((c) => (
        <span
          key={`${c.crop}-${c.layer}`}
          className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${LAYER_COLORS[c.layer]}`}
          title={`${cropLabel(c.crop)} — ${layerLabel(c.layer)}`}
        >
          <span className={`rounded px-1 ${CROP_COLORS[c.crop]}`}>{cropLabel(c.crop)}</span>
          {layerLabel(c.layer)}
        </span>
      ))}
    </div>
  );
}

/* ------- Main ------- */
export default function ExpertManagementPage() {
  const [experts, setExperts] = useState<Expert[]>(INITIAL_EXPERTS);
  const [showAddForm, setShowAddForm] = useState(false);
  const [filterCrop, setFilterCrop] = useState<CropCode | "ALL">("ALL");
  const [filterLayer, setFilterLayer] = useState<LayerCode | "ALL">("ALL");

  /* Add form state */
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [selectedCrops, setSelectedCrops] = useState<Set<CropCode>>(new Set());
  const [selectedLayers, setSelectedLayers] = useState<Set<LayerCode>>(new Set());

  /* Filter */
  const filtered = experts.filter((e) => {
    if (filterCrop === "ALL" && filterLayer === "ALL") return true;
    return e.competencies.some(
      (c) => (filterCrop === "ALL" || c.crop === filterCrop) && (filterLayer === "ALL" || c.layer === filterLayer)
    );
  });

  /* Toggle helpers for checkboxes */
  const toggleCrop = (code: CropCode) => {
    setSelectedCrops((prev) => {
      const next = new Set(prev);
      next.has(code) ? next.delete(code) : next.add(code);
      return next;
    });
  };
  const toggleLayer = (code: LayerCode) => {
    setSelectedLayers((prev) => {
      const next = new Set(prev);
      next.has(code) ? next.delete(code) : next.add(code);
      return next;
    });
  };

  const handleAdd = () => {
    if (!newName.trim() || !newPhone.trim()) return;
    if (selectedCrops.size === 0 || selectedLayers.size === 0) return;
    const competencies: Competency[] = [];
    selectedCrops.forEach((crop) => {
      selectedLayers.forEach((layer) => {
        competencies.push({ crop, layer });
      });
    });
    const expert: Expert = {
      id: `e-${Date.now()}`,
      name: newName.trim(),
      phone: newPhone.trim(),
      competencies,
      reviewCount: 0,
      slaRate: "—",
      status: "Onay Bekliyor",
    };
    setExperts((prev) => [...prev, expert]);
    setNewName("");
    setNewPhone("");
    setSelectedCrops(new Set());
    setSelectedLayers(new Set());
    setShowAddForm(false);
  };

  const handleDelete = (id: string) => setExperts((prev) => prev.filter((e) => e.id !== id));
  const handleApprove = (id: string) => setExperts((prev) => prev.map((e) => (e.id === id ? { ...e, status: "Aktif" as const } : e)));

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
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-900">Yeni Uzman Ekle</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <input placeholder="Ad Soyad" value={newName} onChange={(e) => setNewName(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Telefon" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
          </div>

          {/* Bitki turleri — coklu secim */}
          <div>
            <p className="mb-1.5 text-xs font-semibold text-slate-600">Bitki Turleri (birden fazla secilebilir)</p>
            <div className="flex flex-wrap gap-1.5">
              {CROP_TYPES.map((ct) => (
                <button
                  key={ct.code}
                  type="button"
                  onClick={() => toggleCrop(ct.code)}
                  className={`rounded-full border px-2.5 py-1 text-xs font-medium transition ${selectedCrops.has(ct.code) ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}
                >
                  {ct.label}
                </button>
              ))}
            </div>
          </div>

          {/* Analiz katmanlari — coklu secim */}
          <div>
            <p className="mb-1.5 text-xs font-semibold text-slate-600">Analiz Katmanlari (birden fazla secilebilir)</p>
            <div className="flex flex-wrap gap-1.5">
              {ANALYSIS_LAYERS.map((al) => (
                <button
                  key={al.code}
                  type="button"
                  onClick={() => toggleLayer(al.code)}
                  className={`rounded-full border px-2.5 py-1 text-xs font-medium transition ${selectedLayers.has(al.code) ? "border-emerald-600 bg-emerald-600 text-white" : `border ${LAYER_COLORS[al.code]}`}`}
                >
                  {al.label}
                </button>
              ))}
            </div>
          </div>

          {selectedCrops.size > 0 && selectedLayers.size > 0 && (
            <p className="text-xs text-slate-500">
              {selectedCrops.size} bitki × {selectedLayers.size} katman = {selectedCrops.size * selectedLayers.size} yetkinlik alani olusturulacak
            </p>
          )}

          <button
            onClick={handleAdd}
            disabled={!newName.trim() || !newPhone.trim() || selectedCrops.size === 0 || selectedLayers.size === 0}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Uzman Ekle
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold text-slate-500">Bitki:</span>
          <button onClick={() => setFilterCrop("ALL")} className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${filterCrop === "ALL" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 text-slate-600"}`}>
            Tumu
          </button>
          {CROP_TYPES.map((ct) => (
            <button key={ct.code} onClick={() => setFilterCrop(ct.code)} className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${filterCrop === ct.code ? "border-slate-900 bg-slate-900 text-white" : `border-slate-200 ${CROP_COLORS[ct.code]}`}`}>
              {ct.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold text-slate-500">Katman:</span>
          <button onClick={() => setFilterLayer("ALL")} className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${filterLayer === "ALL" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 text-slate-600"}`}>
            Tumu
          </button>
          {ANALYSIS_LAYERS.map((al) => (
            <button key={al.code} onClick={() => setFilterLayer(al.code)} className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${filterLayer === al.code ? "border-slate-900 bg-slate-900 text-white" : `border ${LAYER_COLORS[al.code]}`}`}>
              {al.label}
            </button>
          ))}
        </div>
      </div>

      {/* Expert table */}
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Uzman</th>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Yetkinlik Alanlari</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">Inceleme</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">SLA</th>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">Islem</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {filtered.map((e) => (
              <tr key={e.id} className="hover:bg-slate-50">
                <td className="px-4 py-2.5">
                  <p className="font-medium text-slate-900">{e.name}</p>
                  <p className="text-xs text-slate-400">{e.phone}</p>
                </td>
                <td className="px-4 py-2.5">
                  <CompetencyTags competencies={e.competencies} />
                </td>
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

      {filtered.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          Bu filtreye uyan uzman bulunmuyor.
        </div>
      )}
    </section>
  );
}
