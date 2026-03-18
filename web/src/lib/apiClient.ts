/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-071: Corr/request header izleri tüm isteklerde taşınır. */
/* KR-081: Typed response contract-first istemci katmanı. */

import { createCorrelationIds, toCorrelationHeaders } from "./correlation";
import { API_TIMEOUT_MS } from "./constants";

export interface ApiRequestOptions extends Omit<RequestInit, "body" | "headers"> {
  readonly body?: unknown;
  readonly headers?: Record<string, string>;
  readonly timeoutMs?: number;
  readonly corrId?: string;
  readonly requestId?: string;
}

export interface ApiResponse<TData> {
  readonly ok: boolean;
  readonly status: number;
  readonly data: TData;
  readonly corrId: string;
  readonly requestId: string;
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly corrId: string;
  public readonly requestId: string;

  constructor(message: string, status: number, corrId: string, requestId: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.corrId = corrId;
    this.requestId = requestId;
  }
}

function normalizeBody(body: unknown): BodyInit | undefined {
  if (body == null) {
    return undefined;
  }
  if (body instanceof FormData || typeof body === "string" || body instanceof URLSearchParams) {
    return body;
  }
  return JSON.stringify(body);
}

export async function apiRequest<TData>(url: string, options: ApiRequestOptions = {}): Promise<ApiResponse<TData>> {
  const timeoutMs = options.timeoutMs ?? API_TIMEOUT_MS;
  const timeoutController = new AbortController();
  const finalController = new AbortController();

  const generatedIds = createCorrelationIds();
  const ids = {
    corrId: options.corrId ?? generatedIds.corrId,
    requestId: options.requestId ?? generatedIds.requestId,
  };

  const timeout = setTimeout(() => timeoutController.abort(), timeoutMs);

  const propagateAbort = () => {
    if (options.signal?.aborted || timeoutController.signal.aborted) {
      finalController.abort();
    }
  };

  options.signal?.addEventListener("abort", propagateAbort);
  timeoutController.signal.addEventListener("abort", propagateAbort);

  try {
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...toCorrelationHeaders(ids),
      ...(options.body != null ? { "Content-Type": "application/json" } : {}),
      ...(options.headers ?? {}),
    };

    // D-3 fix: prepend base URL for relative paths
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    const resolvedUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;

    const response = await fetch(resolvedUrl, {
      ...options,
      headers,
      body: normalizeBody(options.body),
      signal: finalController.signal,
    });

    const rawText = await response.text();
    const parsed = rawText ? (JSON.parse(rawText) as TData) : ({} as TData);

    if (!response.ok) {
      throw new ApiClientError(`API request failed: ${response.status}`, response.status, ids.corrId, ids.requestId);
    }

    return {
      ok: response.ok,
      status: response.status,
      data: parsed,
      corrId: ids.corrId,
      requestId: ids.requestId,
    };
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiClientError("API request timeout/aborted", 408, ids.corrId, ids.requestId);
    }
    throw new ApiClientError("API request failed", 500, ids.corrId, ids.requestId);
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", propagateAbort);
    timeoutController.signal.removeEventListener("abort", propagateAbort);
  }
}
