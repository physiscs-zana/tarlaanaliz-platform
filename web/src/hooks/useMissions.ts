// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-028: Mission yasam dongusu ve SLA alanlari.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface Mission {
  readonly missionId: string;
  readonly fieldId: string;
  readonly status: string;
  readonly missionDate: string;
  readonly pilotId: string | null;
  readonly subscriptionId: string | null;
}

export interface UseMissionsResult {
  readonly missions: readonly Mission[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchMissions: (token: string) => Promise<void>;
}

export function useMissions(): UseMissionsResult {
  const [missions, setMissions] = useState<readonly Mission[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMissions = useCallback(async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ items: Array<{ mission_id: string; field_id: string; status: string; mission_date: string; pilot_id: string | null; subscription_id: string | null }> }>('/missions', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setMissions((res.data?.items ?? []).map(m => ({
        missionId: m.mission_id,
        fieldId: m.field_id,
        status: m.status,
        missionDate: m.mission_date,
        pilotId: m.pilot_id ?? null,
        subscriptionId: m.subscription_id ?? null,
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Görevler yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []);

  return { missions, loading, error, fetchMissions };
}
