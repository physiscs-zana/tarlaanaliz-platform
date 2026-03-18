// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-022: Fiyatlar PriceBook'tan gelir, serbest yazilmaz. Versiyonlu + tarih aralikli.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface PriceBookEntry {
  readonly snapshotId: string;
  readonly cropType: string | null;
  readonly pricePerDonum: number | null;
  readonly validFrom: string;
  readonly validUntil: string | null;
  readonly version: string;
  readonly currency: string;
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
      const res = await apiRequest<{ items: Array<{ snapshot_id: string; crop_type: string | null; price_per_donum: number | null; valid_from: string; valid_until: string | null; version: string; currency: string }> }>('/pricing/active', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setEntries((res.data?.items ?? []).map(e => ({
        snapshotId: e.snapshot_id,
        cropType: e.crop_type ?? null,
        pricePerDonum: e.price_per_donum ?? null,
        validFrom: e.valid_from,
        validUntil: e.valid_until ?? null,
        version: e.version,
        currency: e.currency,
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fiyat bilgisi alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  return { entries, loading, error, fetchPriceBook };
}
