// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-071: Correlation ID üretimi correlation.ts kanonik kaynağından yapılır.

import { createCorrelationIds } from './correlation';
import { getApiBaseUrl } from './api';

export interface HttpRequestOptions extends Omit<RequestInit, 'headers'> {
  headers?: HeadersInit;
  requestId?: string;
  corrId?: string;
  token?: string | null;
}

export async function http<T>(path: string, options?: HttpRequestOptions): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  const ids = createCorrelationIds();
  const requestId = options?.requestId ?? ids.requestId;
  const corrId = options?.corrId ?? ids.corrId;

  let headers: HeadersInit = {
    'content-type': 'application/json',
    'x-request-id': requestId,
    'x-corr-id': corrId,
    ...(options?.headers ?? {})
  };

  if (options?.token) {
    headers = { ...headers, authorization: `Bearer ${options.token}` };
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) throw new Error('Unauthorized');
  if (response.status === 403) throw new Error('Forbidden');
  if (!response.ok) throw new Error('Request failed');

  return (await response.json()) as T;
}
