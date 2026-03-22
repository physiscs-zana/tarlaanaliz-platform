/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-027: Sezonluk Paket — start_date, end_date, interval_days secimi. */
/* KR-015-5: UI'da "Sezonluk Paket" terminolojisi kullanilir. */
/* KR-024: Onerilen tarama periyodu bitki turune gore degisir. */

"use client";

import { FormEvent, useState, useMemo } from "react";

import { apiRequest } from "@/lib/apiClient";

/** KR-027: Sezonluk Paket tarama periyodu seçenekleri (gün). 7 günlük en başta. */
const INTERVAL_OPTIONS = [
  { value: 7, label: "7 Günlük" },
  { value: 10, label: "10 Günlük" },
  { value: 14, label: "14 Günlük" },
  { value: 17, label: "17 Günlük" },
  { value: 21, label: "21 Günlük" },
] as const;

/** KR-024: Bitki bazli onerilen tarama periyotlari (gun). */
const CROP_TYPES = [
  { code: "PAMUK", label: "Pamuk", recommended: 7 },
  { code: "ANTEP_FISTIGI", label: "Antep Fistigi", recommended: 10 },
  { code: "MISIR", label: "Misir", recommended: 14 },
  { code: "BUGDAY", label: "Bugday", recommended: 10 },
  { code: "AYCICEGI", label: "Aycicegi", recommended: 7 },
  { code: "UZUM", label: "Uzum", recommended: 7 },
  { code: "ZEYTIN", label: "Zeytin", recommended: 17 },
  { code: "KIRMIZI_MERCIMEK", label: "Kirmizi Mercimek", recommended: 10 },
] as const;

export default function CreateSubscriptionPage() {
  const [fieldId, setFieldId] = useState("");
  const [cropType, setCropType] = useState("PAMUK");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [intervalDays, setIntervalDays] = useState(7);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedCrop = CROP_TYPES.find(c => c.code === cropType);
  const isNotRecommended = selectedCrop && intervalDays !== selectedCrop.recommended;

  // KR-027: Toplam analiz sayisi hesaplama
  const totalAnalyses = useMemo(() => {
    if (!startDate || !endDate || intervalDays <= 0) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end.getTime() - start.getTime();
    if (diffMs <= 0) return 0;
    return Math.floor(diffMs / (intervalDays * 86400000)) + 1;
  }, [startDate, endDate, intervalDays]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!fieldId.trim()) return setError("Tarla seçimi zorunludur.");
    if (!startDate || !endDate) return setError("Başlangıç ve bitiş tarihi zorunludur.");
    if (intervalDays < 1) return setError("Tarama periyodu en az 1 gün olmalıdır.");

    setIsSubmitting(true);

    try {
      await apiRequest("/subscriptions", {
        method: "POST",
        body: {
          field_id: fieldId.trim(),
          crop_type: cropType,
          start_date: startDate,
          end_date: endDate,
          interval_days: intervalDays,
        },
      });
      setError(null);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Abonelik oluşturulamadı");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Sezonluk Paket Oluştur</h1>

      <form onSubmit={handleSubmit} className="max-w-lg space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="cs-field" className="mb-1 block text-sm font-medium">Tarla (Field ID)</label>
          <input id="cs-field" type="text" required value={fieldId} onChange={(e) => setFieldId(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
        </div>

        <div>
          <label htmlFor="cs-crop" className="mb-1 block text-sm font-medium">Bitki Türü</label>
          <select id="cs-crop" value={cropType} onChange={(e) => setCropType(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2">
            {CROP_TYPES.map((crop) => (
              <option key={crop.code} value={crop.code}>{crop.label}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="cs-start" className="mb-1 block text-sm font-medium">Başlangıç Tarihi</label>
            <input id="cs-start" type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="cs-end" className="mb-1 block text-sm font-medium">Bitiş Tarihi</label>
            <input id="cs-end" type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          </div>
        </div>

        <div>
          <label htmlFor="cs-interval" className="mb-1 block text-sm font-medium">Tarama Periyodu</label>
          <select id="cs-interval" required value={intervalDays} onChange={(e) => setIntervalDays(Number(e.target.value))} className="w-full rounded border border-slate-300 px-3 py-2">
            {INTERVAL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {selectedCrop ? (
            <p className={`mt-1 text-xs ${isNotRecommended ? 'text-amber-600' : 'text-emerald-600'}`}>
              {selectedCrop.label} icin onerilen periyot: {selectedCrop.recommended} gun
              {isNotRecommended ? ' (Farkli bir periyot sectiniz)' : ' (Onerilen periyot secili)'}
            </p>
          ) : null}
        </div>

        {/* KR-027: Toplam analiz sayisi ve fiyat onizleme */}
        {totalAnalyses > 0 ? (
          <div className="rounded border border-blue-200 bg-blue-50 p-3 text-sm space-y-2">
            <p>Toplam tarama sayısı: <strong>{totalAnalyses}</strong></p>
            <p className="text-xs text-slate-500">Fiyat bilgisi ödeme adımında gösterilecektir.</p>
            {/* KR-015-5: Planlanan tarama gunleri onizlemesi */}
            {startDate && endDate && (
              <div className="mt-2 pt-2 border-t border-blue-200">
                <p className="text-xs font-medium text-blue-800 mb-1">Planlanan Tarama Gunleri:</p>
                <div className="flex flex-wrap gap-1">
                  {Array.from({ length: totalAnalyses }, (_, i) => {
                    const d = new Date(startDate);
                    d.setDate(d.getDate() + i * intervalDays);
                    return (
                      <span key={i} className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-mono text-blue-700">
                        {d.toLocaleDateString("tr-TR", { day: "2-digit", month: "2-digit" })}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : null}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button type="submit" disabled={isSubmitting} className="w-full rounded bg-slate-900 px-3 py-2 text-white">
          {isSubmitting ? "Oluşturuluyor..." : "Sezonluk Paketi Başlat"}
        </button>
      </form>
    </section>
  );
}
