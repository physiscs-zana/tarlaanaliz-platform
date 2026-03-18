// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-071: AI çıktıları yalnızca analiz verisi; karar mekanizması değil.
// KR-081: Contract-first tip tanımları.
// KR-018/KR-082 v1.2.0: Graceful Degradation + katmanlı rapor.
// KR-084 v1.2.0: Termal analiz sonuçları (opsiyonel).

import { http } from '@/lib/http';

/** KR-084 v1.2.0: Termal analiz özet verileri. */
export interface ThermalSummary {
  readonly cwsi: number; // 0.0 - 1.0
  readonly canopyTemp: number; // derece C
  readonly canopySoilDeltaT: number;
  readonly irrigationEfficiency: number; // 0.0 - 1.0
}

/** Sonuç katman bilgisi. */
export interface ResultLayer {
  readonly layerName: string;
  readonly layerType: string; // HEALTH | DISEASE | THERMAL_STRESS | ...
  readonly uri: string;
}

export interface ResultData {
  readonly resultId: string;
  readonly missionId: string;
  readonly ndviData: Record<string, unknown> | null;
  readonly ndreData: Record<string, unknown> | null;
  readonly confidenceScore: number;
  readonly resultUrl: string | null;
  readonly createdAtIso: string;
  // KR-018/KR-023 v1.2.0: Graceful Degradation
  readonly reportTier: string; // TEMEL | GENISLETILMIS | KAPSAMLI
  readonly bandClass: string; // BASIC_4BAND | EXTENDED_5BAND
  readonly availableIndices: readonly string[];
  readonly availableLayers: readonly ResultLayer[];
  // KR-084 v1.2.0: Termal (opsiyonel)
  readonly thermalSummary: ThermalSummary | null;
}

export interface ResultListItem {
  readonly resultId: string;
  readonly missionId: string;
  readonly confidenceScore: number;
  readonly createdAtIso: string;
  // KR-023 v1.2.0
  readonly reportTier: string;
  readonly bandClass: string;
}

export interface ResultListResponse {
  readonly items: readonly ResultListItem[];
}

export async function getResult(missionId: string, token: string): Promise<ResultData> {
  return http<ResultData>(`/results/${missionId}/summary`, {
    method: 'GET',
    token,
  });
}

export async function listMissionResults(
  missionId: string,
  token: string
): Promise<ResultListResponse> {
  return http<ResultListResponse>(`/results?mission_id=${encodeURIComponent(missionId)}`, {
    method: 'GET',
    token,
  });
}
