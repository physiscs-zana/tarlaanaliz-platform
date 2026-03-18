"use client";
import { useState } from "react";
const DAYS = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"] as const;
export default function PilotPlannerPage() {
  const [selectedDays, setSelectedDays] = useState<Set<string>>(new Set(["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi"]));
  const [capacity, setCapacity] = useState(2750);
  const [saved, setSaved] = useState(false);
  const toggleDay = (day: string) => { setSelectedDays((prev) => { const next = new Set(prev); next.has(day) ? next.delete(day) : next.add(day); return next; }); };
  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Haftalik Plan</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Calisma Gunleri</p>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((day) => (
              <button key={day} onClick={() => toggleDay(day)} className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${selectedDays.has(day) ? "border-emerald-600 bg-emerald-600 text-white" : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"}`}>{day}</button>
            ))}
          </div>
          <p className="mt-2 text-xs text-slate-500">{selectedDays.size} gun secili</p>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Gunluk Kapasite (donum)</label>
          <input type="number" min={500} max={5000} step={250} value={capacity} onChange={(e) => setCapacity(Number(e.target.value))} className="w-full max-w-xs rounded border border-slate-300 px-3 py-2 text-sm" />
          <p className="mt-1 text-xs text-slate-500">Haftalik toplam: {selectedDays.size * capacity} donum</p>
        </div>
        {saved && <p className="text-sm text-emerald-600">Plan kaydedildi.</p>}
        <button onClick={handleSave} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">Kaydet</button>
      </div>
    </section>
  );
}
