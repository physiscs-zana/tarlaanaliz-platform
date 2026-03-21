/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Web Vitals monitoring (LCP, FID, CLS, TTFB). */

export interface WebVitalMetric {
  name: string;
  value: number;
  delta: number;
  id: string;
  rating?: "good" | "needs-improvement" | "poor";
}

/**
 * Measure the duration of an async API call using the Performance API.
 * Returns the result of the function along with the elapsed time in ms.
 */
export async function measureApiCall<T>(
  name: string,
  fn: () => Promise<T>,
): Promise<{ result: T; durationMs: number }> {
  const markStart = `${name}-start`;
  const markEnd = `${name}-end`;

  if (typeof window !== "undefined" && window.performance) {
    performance.mark(markStart);
  }

  const start = Date.now();
  const result = await fn();
  const durationMs = Date.now() - start;

  if (typeof window !== "undefined" && window.performance) {
    performance.mark(markEnd);
    try {
      performance.measure(name, markStart, markEnd);
    } catch {
      /* measure may fail if marks were cleared */
    }
  }

  if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line no-console
    console.debug(`[perf] ${name}: ${durationMs}ms`);
  }

  return { result, durationMs };
}

/**
 * Report a Web Vital metric.
 * In development, logs to console. In production, sends to the analytics endpoint.
 */
export function reportWebVitals(metric: WebVitalMetric): void {
  if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line no-console
    console.debug(
      `[web-vital] ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating ?? "unknown"})`,
    );
    return;
  }

  /* In production, beacon to analytics endpoint */
  const analyticsUrl = process.env.NEXT_PUBLIC_ANALYTICS_URL;
  if (!analyticsUrl) return;

  try {
    const body = JSON.stringify({
      name: metric.name,
      value: metric.value,
      delta: metric.delta,
      id: metric.id,
      rating: metric.rating,
      timestamp: new Date().toISOString(),
    });

    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      navigator.sendBeacon(analyticsUrl, body);
    } else {
      fetch(analyticsUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {
        /* silently ignore analytics failures */
      });
    }
  } catch {
    /* silently ignore analytics failures */
  }
}
