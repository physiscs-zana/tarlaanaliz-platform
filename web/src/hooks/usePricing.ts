// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-022: Fiyatlar PriceBook'tan gelir, serbest yazilmaz. Versiyonlu + tarih aralikli.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface PriceBookEntry {
  readonly id: string;
  readonly cropType: string;
  readonly pricePerDonum: number;
  readonly validFrom: string;
  readonly validUntil: string | null;
  readonly version: number;
}

export interface UsePricingResult {
  readonly entries: readonly PriceBookEntry[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchPriceBook: (token: string) => Promise<void>;
}

export function usePricing(): UsePricingResult {
  const [entries, setEntries] = useState<readonly PriceBookEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPriceBook = useCallback(async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ items: PriceBookEntry[] }>('/admin/pricing', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setEntries(res.data?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fiyat bilgisi alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  return { entries, loading, error, fetchPriceBook };
}
