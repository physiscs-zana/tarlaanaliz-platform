/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Fiyat yonetimi — bitki turune gore tek seferlik ve sezonluk fiyat belirleme. */
/* CropType VO: PAMUK, ANTEP_FISTIGI, MISIR, BUGDAY, AYCICEGI, UZUM, ZEYTIN, KIRMIZI_MERCIMEK */

"use client";

import { useState } from "react";

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

interface CropPrice {
  cropCode: string;
  cropLabel: string;
  singlePricePerHa: number;
  seasonalPricePerHa: number;
  seasonalInterval: number;
}

const INITIAL_PRICES: CropPrice[] = CROP_TYPES.map((ct) => ({
  cropCode: ct.code,
  cropLabel: ct.label,
  singlePricePerHa: 250,
  seasonalPricePerHa: 120,
  seasonalInterval: ct.code === "PAMUK" || ct.code === "AYCICEGI" || ct.code === "UZUM" ? 7
    : ct.code === "MISIR" || ct.code === "ZEYTIN" ? 15
    : 10,
}));

export default function PriceManagementPage() {
  const [prices, setPrices] = useState<CropPrice[]>(INITIAL_PRICES);
  const [saved, setSaved] = useState(false);

  const updatePrice = (cropCode: string, field: keyof CropPrice, value: number) => {
    setPrices((prev) =>
      prev.map((p) => (p.cropCode === cropCode ? { ...p, [field]: value } : p))
    );
    setSaved(false);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Fiyat Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Bitki turune gore tek seferlik ve sezonluk analiz fiyatlarini belirleyin.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Fiyatlari Kaydet
        </button>
      </div>

      {saved && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          Fiyatlar kaydedildi.
        </div>
      )}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Bitki Turu</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Tek Seferlik (TL/ha)</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Sezonluk (TL/ha)</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Tarama Periyodu (gun)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {prices.map((p) => (
              <tr key={p.cropCode} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{p.cropLabel}</td>
                <td className="px-4 py-3 text-right">
                  <input
                    type="number"
                    min={0}
                    step={10}
                    value={p.singlePricePerHa}
                    onChange={(e) => updatePrice(p.cropCode, "singlePricePerHa", Number(e.target.value))}
                    className="w-24 rounded border border-slate-300 px-2 py-1 text-right text-sm"
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  <input
                    type="number"
                    min={0}
                    step={10}
                    value={p.seasonalPricePerHa}
                    onChange={(e) => updatePrice(p.cropCode, "seasonalPricePerHa", Number(e.target.value))}
                    className="w-24 rounded border border-slate-300 px-2 py-1 text-right text-sm"
                  />
                </td>
                <td className="px-4 py-3 text-right">
                  <input
                    type="number"
                    min={1}
                    max={30}
                    value={p.seasonalInterval}
                    onChange={(e) => updatePrice(p.cropCode, "seasonalInterval", Number(e.target.value))}
                    className="w-20 rounded border border-slate-300 px-2 py-1 text-right text-sm"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400">
        Fiyat degisiklikleri sadece CENTRAL_ADMIN tarafindan yayinlanabilir. Tum degisiklikler audit log&apos;a kaydedilir.
      </p>
    </section>
  );
}
