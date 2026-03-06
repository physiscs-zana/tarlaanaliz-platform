// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// BOLUM 3: Gozlemlenebilirlik — audit log sorgulama.

import { useCallback, useState } from 'react';

import { apiRequest } from '@/lib/apiClient';

export interface AuditLogEntry {
  readonly id: string;
  readonly eventName: string;
  readonly actor: string;
  readonly timestamp: string;
  readonly correlationId: string;
  readonly metadata: Record<string, unknown>;
}

export interface UseAuditLogsResult {
  readonly logs: readonly AuditLogEntry[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly fetchLogs: (token: string, filters?: { eventName?: string }) => Promise<void>;
}

export function useAuditLogs(): UseAuditLogsResult {
  const [logs, setLogs] = useState<readonly AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async (token: string, filters?: { eventName?: string }) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters?.eventName) params.set('event_name', filters.eventName);
      const qs = params.toString();
      const url = `/admin/audit${qs ? `?${qs}` : ''}`;
      const res = await apiRequest<{ items: AuditLogEntry[] }>(url, { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      setLogs(res.data?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audit logları yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []);

  return { logs, loading, error, fetchLogs };
}
