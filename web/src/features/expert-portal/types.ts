/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: Contract-first tip tanımları. */

export type QueueItemStatus = "queued" | "in_review" | "completed";

export interface ExpertQueueItem {
  readonly reviewId: string;
  readonly missionId: string;
  readonly fieldName: string;
  readonly priority: "low" | "medium" | "high";
  readonly status: QueueItemStatus;
  readonly createdAtIso: string;
  // KR-018/KR-023 v1.2.0: Graceful Degradation bilgisi
  readonly bandClass: string; // BASIC_4BAND | EXTENDED_5BAND
  readonly reportTier: string; // TEMEL | GENISLETILMIS | KAPSAMLI
}

export interface ExpertQueueStats {
  readonly total: number;
  readonly queued: number;
  readonly inReview: number;
  readonly completed: number;
}

export interface ExpertReviewDetail {
  readonly reviewId: string;
  readonly missionId: string;
  readonly notes: string;
  readonly createdAtIso: string;
  readonly updatedAtIso: string;
}

export interface CorrelationMeta {
  readonly corrId: string;
  readonly requestId: string;
}
