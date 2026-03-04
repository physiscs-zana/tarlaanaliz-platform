/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: Route param ve response contract-first tiplerle ele alınır. */
/* KR-071: corr/request metadata response ile taşınır. */

import type { Metadata } from "next";

import { getReviewDetail } from "@/features/expert-portal/services/expertReviewService";
import type { ExpertReviewDetail } from "@/features/expert-portal/types";
import { COOKIE_TOKEN_KEY } from "@/lib/constants";
import { cookies } from "next/headers";

interface ReviewPageParams {
  readonly reviewId: string;
}

interface ReviewPageProps {
  readonly params: ReviewPageParams;
}

export const metadata: Metadata = {
  title: "Expert Review",
};

export default async function ExpertReviewDetailPage({ params }: ReviewPageProps) {
  const reviewId = params.reviewId;
  const token = cookies().get(COOKIE_TOKEN_KEY)?.value ?? "";

  let review: ExpertReviewDetail | null = null;
  try {
    review = await getReviewDetail(reviewId, token);
  } catch {
    review = null;
  }

  return (
    <section aria-label="Expert review detail" className="space-y-4" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Review Detayı</h1>
      {review ? (
        <article className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <p>Review ID: {review.reviewId}</p>
          <p>Mission ID: {review.missionId}</p>
          <p>Not: {review.notes}</p>
        </article>
      ) : (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">Detay verisi henüz alınamadı.</p>
      )}
    </section>
  );
}
