/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-027: Sezonluk Paket — start_date, end_date, interval_days secimi. */
/* KR-015-5: UI'da "Sezonluk Paket" terminolojisi kullanilir. */
/* KR-024: Onerilen tarama periyodu bitki turune gore degisir. */

"use client";

import { FormEvent, useState, useMemo } from "react";

import { apiRequest } from "@/lib/apiClient";

/** KR-024: Bitki bazli onerilen tarama periyotlari (gun). */
const CROP_INTERVALS: Record<string, { min: number; max: number }> = {
  Pamuk: { min: 7, max: 10 },
  "Antep Fıstığı": { min: 10, max: 15 },
  Mısır: { min: 15, max: 20 },
  Buğday: { min: 10, max: 15 },
  Ayçiçeği: { min: 7, max: 10 },
  Üzüm: { min: 7, max: 10 },
  Zeytin: { min: 15, max: 20 },
  "Kırmızı Mercimek": { min: 10, max: 15 },
};

interface CreateSubscriptionPayload {
  readonly fieldId: string;
  readonly cropType: string;
  readonly startDate: string;
  readonly endDate: string;
  readonly intervalDays: number;
}

export default function CreateSubscriptionPage() {
  const [fieldId, setFieldId] = useState("");
  const [cropType, setCropType] = useState("Pamuk");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [intervalDays, setIntervalDays] = useState(7);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const suggestedInterval = CROP_INTERVALS[cropType];
  const isIntervalOutOfRange = suggestedInterval && (intervalDays < suggestedInterval.min || intervalDays > suggestedInterval.max);

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

    const payload: CreateSubscriptionPayload = {
      fieldId: fieldId.trim(),
      cropType,
      startDate,
      endDate,
      intervalDays,
    };

    try {
      await apiRequest("/api/subscriptions", { method: "POST", body: payload });
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
            {Object.keys(CROP_INTERVALS).map((crop) => (
              <option key={crop} value={crop}>{crop}</option>
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
          <label htmlFor="cs-interval" className="mb-1 block text-sm font-medium">Tarama Periyodu (gün)</label>
          <input id="cs-interval" type="number" min={1} max={30} required value={intervalDays} onChange={(e) => setIntervalDays(Number(e.target.value))} className="w-full rounded border border-slate-300 px-3 py-2" />
          {suggestedInterval ? (
            <p className={`mt-1 text-xs ${isIntervalOutOfRange ? 'text-amber-600' : 'text-slate-500'}`}>
              {cropType} için önerilen periyot: {suggestedInterval.min}–{suggestedInterval.max} gün
              {isIntervalOutOfRange ? ' (Önerilen aralık dışında!)' : ''}
            </p>
          ) : null}
        </div>

        {/* KR-027: Toplam analiz sayisi ve fiyat onizleme */}
        {totalAnalyses > 0 ? (
          <div className="rounded border border-blue-200 bg-blue-50 p-3 text-sm">
            <p>Toplam tarama sayısı: <strong>{totalAnalyses}</strong></p>
            <p className="text-xs text-slate-500 mt-1">Fiyat bilgisi ödeme adımında gösterilecektir.</p>
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
