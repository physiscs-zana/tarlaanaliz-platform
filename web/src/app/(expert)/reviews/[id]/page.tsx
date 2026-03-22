/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Uzman inceleme detay ve karar verme sayfasi. */
/* KR-029: Training grade (A-D|REJECT) + grade_reason. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";
import { VerdictForm, type VerdictPayload } from "@/features/expert-portal/components/VerdictForm";

interface ReviewDetail {
  review_id: string;
  mission_id: string;
  analysis_result_id: string;
  status: string;
  assigned_at: string;
  started_at: string | null;
  completed_at: string | null;
  verdict: string | null;
  training_grade: string | null;
  grade_reason: string | null;
}

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  PENDING: { label: "Bekliyor", cls: "bg-amber-100 text-amber-800" },
  IN_PROGRESS: { label: "Inceleniyor", cls: "bg-blue-100 text-blue-800" },
  COMPLETED: { label: "Tamamlandi", cls: "bg-emerald-100 text-emerald-800" },
  REJECTED: { label: "Reddedildi", cls: "bg-rose-100 text-rose-800" },
};

export default function ExpertReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reviewId = params?.id as string;

  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const fetchReview = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      // Kuyruktan bu review'i bul
      const res = await fetch(`${baseUrl}/expert-portal/reviews/queue?limit=100`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setError("Inceleme yuklenemedi"); return; }
      const items = (await res.json()) as ReviewDetail[];
      const found = items.find((r) => r.review_id === reviewId);
      setReview(found ?? null);
      if (!found) setError("Bu inceleme bulunamadi veya size atanmamis.");
    } catch { setError("Baglanti hatasi."); } finally { setLoading(false); }
  }, [reviewId]);

  useEffect(() => { fetchReview(); }, [fetchReview]);

  const handleSubmitVerdict = useCallback(async (payload: VerdictPayload) => {
    const token = getTokenFromCookie();
    if (!token) return;
    const baseUrl = getApiBaseUrl();

    const res = await fetch(`${baseUrl}/expert-portal/reviews/${reviewId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        decision: payload.decision,
        notes: payload.summary,
        training_grade: payload.trainingGrade,
        grade_reason: payload.gradeReason,
      }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error((body as { detail?: string }).detail || "Karar gonderilemedi.");
    }
    setSubmitted(true);
  }, [reviewId]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;
  if (error) return <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>;
  if (!review) return <div className="py-12 text-center text-sm text-slate-500">Inceleme bulunamadi.</div>;

  const si = STATUS_LABELS[review.status] ?? { label: review.status, cls: "bg-slate-100 text-slate-600" };
  const isEditable = review.status === "PENDING" || review.status === "IN_PROGRESS";

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Inceleme Detayi</h1>
        <button onClick={() => router.push("/queue")} className="rounded bg-slate-100 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-200">
          Kuyruga Don
        </button>
      </div>

      {/* Inceleme bilgileri */}
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-sm text-slate-600">#{review.review_id.slice(0, 12)}</span>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${si.cls}`}>{si.label}</span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-slate-500">Gorev ID:</span>
            <span className="ml-2 font-mono text-xs">{review.mission_id.slice(0, 12)}</span>
          </div>
          <div>
            <span className="text-slate-500">Analiz Sonucu:</span>
            <span className="ml-2 font-mono text-xs">{review.analysis_result_id.slice(0, 12)}</span>
          </div>
          <div>
            <span className="text-slate-500">Atanma:</span>
            <span className="ml-2">{review.assigned_at ? new Date(review.assigned_at).toLocaleString("tr-TR") : "—"}</span>
          </div>
          {review.completed_at && (
            <div>
              <span className="text-slate-500">Tamamlanma:</span>
              <span className="ml-2">{new Date(review.completed_at).toLocaleString("tr-TR")}</span>
            </div>
          )}
        </div>

        {/* Onceki karar (tamamlanmissa) */}
        {review.verdict && (
          <div className="rounded border border-emerald-200 bg-emerald-50 p-3 text-sm space-y-1">
            <p><strong>Karar:</strong> {review.verdict}</p>
            {review.training_grade && <p><strong>Not:</strong> {review.training_grade}</p>}
            {review.grade_reason && <p><strong>Gerekce:</strong> {review.grade_reason}</p>}
          </div>
        )}
      </div>

      {/* Karar formu */}
      {submitted ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-center space-y-2">
          <p className="text-lg font-medium text-emerald-800">Karar basariyla gonderildi</p>
          <button onClick={() => router.push("/queue")} className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700">
            Kuyruga Don
          </button>
        </div>
      ) : isEditable ? (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold mb-4">Karar Ver</h2>
          <VerdictForm reviewId={reviewId} onSubmitVerdict={handleSubmitVerdict} />
        </div>
      ) : null}
    </section>
  );
}
