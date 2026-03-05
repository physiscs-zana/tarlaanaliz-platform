// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: Odeme + Manuel Onay + Audit akisi.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';
import type { PaymentStatus } from '@/components/features/payment/PaymentStatusBadge';

export interface PaymentIntent {
  readonly id: string;
  readonly memberId: string;
  readonly fieldId: string | null;
  readonly status: PaymentStatus;
  readonly amount: number;
  readonly receiptBlobId: string | null;
  readonly createdAt: string;
}

export interface UseAdminPaymentsResult {
  readonly intents: readonly PaymentIntent[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchPending: (token: string) => Promise<void>;
  readonly markPaid: (intentId: string, adminNote: string, token: string) => Promise<void>;
  readonly reject: (intentId: string, reason: string, token: string) => Promise<void>;
}

export function useAdminPayments(): UseAdminPaymentsResult {
  const [intents, setIntents] = useState<readonly PaymentIntent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPending = useCallback(async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiRequest<{ items: PaymentIntent[] }>('/admin/payments/intents?status=PAYMENT_PENDING', { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setIntents(res.data?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ödeme listesi alınamadı');
    } finally {
      setLoading(false);
    }
  }, []);

  const markPaid = useCallback(async (intentId: string, adminNote: string, token: string) => {
    await apiRequest(`/admin/payments/intents/${encodeURIComponent(intentId)}/mark-paid`, { method: 'POST', body: { admin_note: adminNote }, headers: { Authorization: `Bearer ${token}` } });
  }, []);

  const reject = useCallback(async (intentId: string, reason: string, token: string) => {
    await apiRequest(`/admin/payments/intents/${encodeURIComponent(intentId)}/reject`, { method: 'POST', body: { rejection_reason: reason }, headers: { Authorization: `Bearer ${token}` } });
  }, []);

  return { intents, loading, error, fetchPending, markPaid, reject };
}
