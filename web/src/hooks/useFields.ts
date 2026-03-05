// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-013: Tarla kaydi ve yonetimi.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface Field {
  readonly id: string;
  readonly province: string;
  readonly district: string;
  readonly village: string;
  readonly block: string;
  readonly parcel: string;
  readonly areaM2: number;
  readonly cropType: string;
}

export interface UseFieldsResult {
  readonly fields: readonly Field[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchFields: (token: string) => Promise<void>;
}

export function useFields(): UseFieldsResult {
  const [fields, setFields] = useState<readonly Field[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFields = useCallback(async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ items: Field[] }>('/fields', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setFields(res.data?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tarlalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []);

  return { fields, loading, error, fetchFields };
}
