/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Offline queue hook; queue actions, sync on reconnect. */

"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "ta_offline_queue";

export interface QueuedOperation {
  id: string;
  url: string;
  method: "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  createdAt: string;
}

function loadQueue(): QueuedOperation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as QueuedOperation[]) : [];
  } catch {
    return [];
  }
}

function saveQueue(ops: QueuedOperation[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ops));
  } catch {
    /* localStorage may be full — silently fail */
  }
}

export function useOfflineQueue() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );
  const [pendingCount, setPendingCount] = useState(0);

  /* Sync pending count from storage */
  const syncCount = useCallback(() => {
    setPendingCount(loadQueue().length);
  }, []);

  /* Listen to online/offline events */
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    syncCount();

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [syncCount]);

  /* Enqueue an operation for later execution */
  const enqueue = useCallback(
    (op: Omit<QueuedOperation, "id" | "createdAt">) => {
      const queue = loadQueue();
      const entry: QueuedOperation = {
        ...op,
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        createdAt: new Date().toISOString(),
      };
      queue.push(entry);
      saveQueue(queue);
      setPendingCount(queue.length);
    },
    [],
  );

  /* Flush the queue — attempt each operation in order */
  const flush = useCallback(async () => {
    const queue = loadQueue();
    if (queue.length === 0) return;

    const failed: QueuedOperation[] = [];

    for (const op of queue) {
      try {
        const res = await fetch(op.url, {
          method: op.method,
          headers: op.headers ?? { "Content-Type": "application/json" },
          body: op.body ? JSON.stringify(op.body) : undefined,
        });
        if (!res.ok) {
          failed.push(op);
        }
      } catch {
        failed.push(op);
      }
    }

    saveQueue(failed);
    setPendingCount(failed.length);
  }, []);

  /* Auto-flush when we come back online */
  useEffect(() => {
    if (isOnline && pendingCount > 0) {
      flush();
    }
  }, [isOnline, pendingCount, flush]);

  return { isOnline, pendingCount, enqueue, flush };
}
