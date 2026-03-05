// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-019: Expert portal review kuyruğu; SLA 4 saat.
// Kanonik kaynak: useExpertQueue.ts — aynı API endpoint (listPendingReviews).
// Bu dosya geriye dönük uyumluluk için useExpertQueue'yu sarmalayan facade'dir.
'use client';

import { useExpertQueue } from './useExpertQueue';
import type { UseExpertQueueResult } from './useExpertQueue';

export interface UseExpertReviewsResult {
  readonly reviews: UseExpertQueueResult['items'];
  readonly isLoading: boolean;
  readonly error: string | null;
  readonly refetch: () => Promise<void>;
}

export function useExpertReviews(token: string | null): UseExpertReviewsResult {
  const queue = useExpertQueue(token);
  return {
    reviews: queue.items,
    isLoading: queue.isLoading,
    error: queue.error,
    refetch: queue.refetch,
  };
}
