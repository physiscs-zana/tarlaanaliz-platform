/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Feedback kalite gostergesi. */

"use client";

export type FeedbackGrade = "A" | "B" | "C" | "D" | "REJECT";

export interface FeedbackQualityIndicatorProps {
  grade: FeedbackGrade;
  confidence?: number;
}

const gradeConfig: Record<
  FeedbackGrade,
  { label: string; className: string }
> = {
  A: {
    label: "A — Mükemmel",
    className: "bg-emerald-100 text-emerald-800 border-emerald-300",
  },
  B: {
    label: "B — İyi",
    className: "bg-sky-100 text-sky-800 border-sky-300",
  },
  C: {
    label: "C — Orta",
    className: "bg-amber-100 text-amber-800 border-amber-300",
  },
  D: {
    label: "D — Zayıf",
    className: "bg-orange-100 text-orange-800 border-orange-300",
  },
  REJECT: {
    label: "Reddedildi",
    className: "bg-rose-100 text-rose-800 border-rose-300",
  },
};

export function FeedbackQualityIndicator({
  grade,
  confidence,
}: FeedbackQualityIndicatorProps) {
  const config = gradeConfig[grade];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${config.className}`}
    >
      {config.label}
      {confidence !== undefined && (
        <span className="text-[10px] font-normal opacity-75">
          %{Math.round(confidence * 100)}
        </span>
      )}
    </span>
  );
}
