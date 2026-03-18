// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-019: Expert portal review akışı; güven eşiği aşılmayan sonuçlar kuyruğa girer.
// KR-081: Contract-first tip tanımları — types.ts kanonik kaynaktır.

import { http } from '@/lib/http';
import type { ExpertQueueItem, ExpertReviewDetail } from '../types';

/** PendingReviewItem artık ExpertQueueItem ile aynıdır (types.ts kanonik kaynak). */
export type PendingReviewItem = ExpertQueueItem;

export interface PendingReviewsResponse {
  readonly items: readonly PendingReviewItem[];
}

export interface ExpertReviewPayload {
  readonly confidenceAdjustment: number;
  readonly reviewNotes: string;
  readonly approved: boolean;
}

export async function listPendingReviews(token: string): Promise<PendingReviewsResponse> {
  return http<PendingReviewsResponse>('/expert-portal/reviews', {
    method: 'GET',
    token,
  });
}

export async function getReviewDetail(reviewId: string, token: string): Promise<ExpertReviewDetail> {
  return http<ExpertReviewDetail>(`/expert-portal/reviews/${reviewId}`, {
    method: 'GET',
    token,
  });
}

export async function submitReview(
  reviewId: string,
  payload: ExpertReviewPayload,
  token: string
): Promise<void> {
  await http<void>(`/expert-portal/reviews/${reviewId}/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
    token,
  });
}
