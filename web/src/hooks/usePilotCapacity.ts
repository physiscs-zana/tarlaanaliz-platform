// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-015-1: Pilot calisma gunleri ve gunluk kapasite tanimi.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface PilotCapacity {
  readonly workDays: readonly string[];
  readonly dailyCapacityDonum: number;
}

export interface UsePilotCapacityResult {
  readonly capacity: PilotCapacity | null;
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchCapacity: (token: string) => Promise<void>;
}

const DEFAULT_CAPACITY: PilotCapacity = {
  workDays: [],
  dailyCapacityDonum: 2750,
};

export function usePilotCapacity(): UsePilotCapacityResult {
  const [capacity, setCapacity] = useState<PilotCapacity | null>(DEFAULT_CAPACITY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCapacity = useCallback(async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ work_days: string[]; daily_capacity_donum: number }>('/pilots/me/capacity', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      const d = res.data;
      setCapacity(d ? { workDays: d.work_days, dailyCapacityDonum: d.daily_capacity_donum } : DEFAULT_CAPACITY);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Kapasite bilgisi alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  return { capacity, loading, error, fetchCapacity };
}
