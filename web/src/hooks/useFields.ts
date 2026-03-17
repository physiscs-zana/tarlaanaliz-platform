// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-013: Tarla kaydi ve yonetimi.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface Field {
  readonly fieldId: string;
  readonly fieldName: string;
  readonly parcelRef: string;
  readonly areaHa: number;
  readonly cropType: string | null;
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
      const res = await apiRequest<{ items: Array<{ field_id: string; field_name: string; parcel_ref: string; area_ha: number; crop_type: string | null }> }>('/fields', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setFields((res.data?.items ?? []).map(f => ({
        fieldId: f.field_id,
        fieldName: f.field_name,
        parcelRef: f.parcel_ref,
        areaHa: f.area_ha,
        cropType: f.crop_type ?? null,
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tarlalar yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []);

  return { fields, loading, error, fetchFields };
}
