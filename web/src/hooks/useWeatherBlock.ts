// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-015-3A: Pilot ucus otoritesi — "Ucus yapilamiyor" bildirimi.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface WeatherBlockReport {
  readonly missionId: string;
  readonly reportedAt: string;
  readonly reason: string;
}

export interface UseWeatherBlockResult {
  readonly submitting: boolean;
  readonly error: string | null;
  readonly success: boolean;
  readonly submitBlock: (report: WeatherBlockReport, token: string) => Promise<void>;
}

export function useWeatherBlock(): UseWeatherBlockResult {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const submitBlock = useCallback(async (report: WeatherBlockReport, token: string) => {
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest('/api/pilot/weather-block', { method: 'POST', body: report, headers: { Authorization: `Bearer ${token}` } });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bildirim gönderilemedi');
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { submitting, error, success, submitBlock };
}
