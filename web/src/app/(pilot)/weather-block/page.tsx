/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015-3A: Pilot ucus otoritesi — "Ucus yapilamiyor" bildirimi. */
/* Zorunlu alanlar: mission_id, reported_at, reason */

"use client";

import { FormEvent, useState } from "react";

import { apiRequest } from "@/lib/apiClient";

interface WeatherBlockPayload {
  readonly missionId: string;
  readonly reportedAt: string;
  readonly reason: string;
}

export default function WeatherBlockPage() {
  const [missionId, setMissionId] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(false);

    if (!missionId.trim()) return setError("Görev seçimi zorunludur.");
    if (!reason.trim()) return setError("Gerekçe zorunludur.");

    setIsSubmitting(true);

    const payload: WeatherBlockPayload = {
      missionId: missionId.trim(),
      reportedAt: new Date().toISOString(),
      reason: reason.trim(),
    };

    try {
      await apiRequest("/api/pilot/weather-block", {
        method: "POST",
        body: payload,
      });
      setSuccess(true);
      setReason("");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Bildirim gönderilemedi");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="space-y-4" aria-label="Weather block report">
      <h1 className="text-2xl font-semibold">Uçuş Yapılamıyor Bildirimi</h1>
      <p className="text-sm text-slate-600">
        KR-015-3A: Sahadaki gerçek koşulları gözlemleyen tek yetkili kişi pilottur. Bu bildirim sisteme girildiği anda kabul edilir; doğrulama aşaması yoktur.
      </p>

      {success ? (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          Bildiriminiz kaydedildi. Görev ertelenmiştir ve çiftçiye bildirim gönderilecektir.
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="max-w-md space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label htmlFor="wb-mission" className="mb-1 block text-sm font-medium">Görev (Mission ID)</label>
          <input
            id="wb-mission"
            name="missionId"
            type="text"
            required
            value={missionId}
            onChange={(e) => setMissionId(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2"
            placeholder="Örn: MSN-2026-001"
          />
        </div>
        <div>
          <label htmlFor="wb-reason" className="mb-1 block text-sm font-medium">Gerekçe</label>
          <textarea
            id="wb-reason"
            name="reason"
            required
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2"
            placeholder="Kötü hava, teknik arıza, güvenlik vb."
          />
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <button type="submit" disabled={isSubmitting} className="rounded bg-red-600 px-4 py-2 text-white disabled:opacity-70">
          {isSubmitting ? "Gönderiliyor..." : "Uçuş Yapılamıyor Bildir"}
        </button>
      </form>
    </section>
  );
}
