/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Verdict format: confirmed | corrected | rejected | needs_more_expert */
/* KR-019: training_grade: A|B|C|D|REJECT + grade_reason (max 200 karakter) */
/* KR-081: Verdict payload contract-first tip ile üretilir. */

import { FormEvent, useState } from "react";

/** KR-019: Kanonik uzman karar enum'u (SSOT ile birebir). */
export type VerdictDecision = "confirmed" | "corrected" | "rejected" | "needs_more_expert";

/** KR-019: Eğitim kalite notu (SSOT ile birebir). */
export type TrainingGrade = "A" | "B" | "C" | "D" | "REJECT";

export interface VerdictPayload {
  readonly reviewId: string;
  readonly decision: VerdictDecision;
  readonly summary: string;
  readonly trainingGrade: TrainingGrade;
  readonly gradeReason: string;
  readonly corrId?: string;
  readonly requestId?: string;
}

export interface VerdictFormProps {
  readonly reviewId: string;
  readonly corrId?: string;
  readonly requestId?: string;
  readonly onSubmitVerdict: (payload: VerdictPayload) => Promise<void>;
}

const GRADE_REASON_MAX_LENGTH = 200;

const DECISION_LABELS: Record<VerdictDecision, string> = {
  confirmed: "Onayla (Confirmed)",
  corrected: "Düzeltildi (Corrected)",
  rejected: "Reddet (Rejected)",
  needs_more_expert: "Ek Uzman Gerekli",
};

const GRADE_LABELS: Record<TrainingGrade, string> = {
  A: "A — Mükemmel",
  B: "B — İyi",
  C: "C — Orta",
  D: "D — Zayıf",
  REJECT: "REJECT — Kullanılamaz",
};

export function VerdictForm({ reviewId, corrId, requestId, onSubmitVerdict }: VerdictFormProps) {
  const [decision, setDecision] = useState<VerdictDecision>("confirmed");
  const [summary, setSummary] = useState("");
  const [trainingGrade, setTrainingGrade] = useState<TrainingGrade>("B");
  const [gradeReason, setGradeReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!summary.trim()) return;
    if (!gradeReason.trim()) return;

    setSubmitting(true);
    try {
      await onSubmitVerdict({
        reviewId,
        decision,
        summary: summary.trim(),
        trainingGrade,
        gradeReason: gradeReason.trim().slice(0, GRADE_REASON_MAX_LENGTH),
        corrId,
        requestId,
      });
      setSummary("");
      setGradeReason("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" data-corr-id={corrId} data-request-id={requestId}>
      {/* KR-019: Verdict Decision */}
      <fieldset>
        <legend className="mb-1 font-medium">Karar</legend>
        {(Object.entries(DECISION_LABELS) as [VerdictDecision, string][]).map(([value, label]) => (
          <label key={value} className="mr-3 inline-flex items-center gap-1">
            <input
              type="radio"
              name="decision"
              value={value}
              checked={decision === value}
              onChange={() => setDecision(value)}
            />
            {label}
          </label>
        ))}
      </fieldset>

      {/* KR-019: Expert Notu */}
      <div>
        <label htmlFor="verdict-summary" className="mb-1 block font-medium">
          Expert Notu
        </label>
        <textarea
          id="verdict-summary"
          name="summary"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
          rows={4}
          required
          className="w-full rounded border p-2"
        />
      </div>

      {/* KR-019: Training Grade */}
      <div>
        <label htmlFor="training-grade" className="mb-1 block font-medium">
          Eğitim Kalite Notu (Training Grade)
        </label>
        <select
          id="training-grade"
          name="trainingGrade"
          value={trainingGrade}
          onChange={(event) => setTrainingGrade(event.target.value as TrainingGrade)}
          className="w-full rounded border p-2"
          required
        >
          {(Object.entries(GRADE_LABELS) as [TrainingGrade, string][]).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* KR-019: Grade Reason (max 200 karakter) */}
      <div>
        <label htmlFor="grade-reason" className="mb-1 block font-medium">
          Kalite Notu Gerekçesi ({gradeReason.length}/{GRADE_REASON_MAX_LENGTH})
        </label>
        <textarea
          id="grade-reason"
          name="gradeReason"
          value={gradeReason}
          onChange={(event) => setGradeReason(event.target.value.slice(0, GRADE_REASON_MAX_LENGTH))}
          rows={2}
          required
          maxLength={GRADE_REASON_MAX_LENGTH}
          className="w-full rounded border p-2"
        />
      </div>

      <button type="submit" disabled={submitting} className="rounded border px-3 py-2 disabled:opacity-70">
        {submitting ? "Gönderiliyor..." : "Kararı Gönder"}
      </button>
    </form>
  );
}
