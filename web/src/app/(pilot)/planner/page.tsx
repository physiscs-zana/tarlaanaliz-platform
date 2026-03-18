/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: kapasite/calisma gunu kisitlari. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

const DAYS = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"] as const;

export default function PilotPlannerPage() {
  const [selectedDays, setSelectedDays] = useState<Set<string>>(new Set());
  const [capacity, setCapacity] = useState(2750);
  const [saved, setSaved] = useState(false);
  const [locked, setLocked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlan = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/me/capacity`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as { work_days: string[]; daily_capacity_donum: number; locked?: boolean };
        if (data.work_days && data.work_days.length > 0) {
          setSelectedDays(new Set(data.work_days));
          setCapacity(data.daily_capacity_donum);
          setLocked(data.locked ?? true);
        }
      }
    } catch { /* ignore */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchPlan(); }, [fetchPlan]);

  const toggleDay = (day: string) => {
    if (locked) return;
    setSelectedDays((prev) => { const next = new Set(prev); next.has(day) ? next.delete(day) : next.add(day); return next; });
  };

  const handleSave = async () => {
    if (locked) return;
    setError(null);
    if (selectedDays.size === 0) { setError("En az bir calisma gunu secilmelidir."); return; }
    if (selectedDays.size > 6) { setError("En fazla 6 gun secilebilir."); return; }

    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/me/capacity`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ work_days: Array.from(selectedDays), daily_capacity_donum: capacity }),
      });
      if (res.ok) {
        setSaved(true);
        setLocked(true);
        setTimeout(() => setSaved(false), 2000);
      } else {
        const body = await res.json().catch(() => ({}));
        setError((body as { detail?: string }).detail || "Plan kaydedilemedi.");
      }
    } catch { setError("Baglanti hatasi."); }
  };

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Haftalik Plan</h1>

      {/* KR-015: Kapasite bilgilendirme */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
        <h3 className="font-semibold">Kapasite Kurallari</h3>
        <ul className="mt-1 list-inside list-disc text-xs">
          <li>Calisma gunleri: en fazla 6 gun/hafta</li>
          <li>Gunluk kapasite: 2750 donum/gun (varsayilan, aralik: 2500-3000)</li>
          <li>Kapasite asim toleransi: yalnizca acil durumda %10 (maks. 3300 donum)</li>
        </ul>
      </div>

      {locked && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <strong>Uyari:</strong> Haftalik plan secimi yalnizca bir kez yapilabilir. Degisiklik icin Central Admin onayi gereklidir.
          Degisiklik talep etmek icin yoneticinize basvurunuz.
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Calisma Gunleri</p>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((day) => (
              <button
                key={day}
                onClick={() => toggleDay(day)}
                disabled={locked}
                className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${selectedDays.has(day) ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"} ${locked ? "opacity-60 cursor-not-allowed" : ""}`}
              >
                {day}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-slate-500">{selectedDays.size} gun secili</p>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Gunluk Kapasite (donum)</label>
          <input
            type="number"
            min={2500}
            max={3000}
            step={250}
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
            disabled={locked}
            className={`w-full max-w-xs rounded border border-slate-300 px-3 py-2 text-sm ${locked ? "opacity-60 cursor-not-allowed bg-slate-100" : ""}`}
          />
          <p className="mt-1 text-xs text-slate-500">Haftalik toplam: {selectedDays.size * capacity} donum</p>
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        {saved && <p className="text-sm text-emerald-600">Plan kaydedildi.</p>}
        {!locked && (
          <button onClick={handleSave} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">
            Kaydet
          </button>
        )}
      </div>
    </section>
  );
}
