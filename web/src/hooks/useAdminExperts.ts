/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Admin expert management hook (curated onboarding). */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

export interface Expert {
  expert_id: string;
  full_name: string;
  email: string;
  phone: string;
  province: string;
  status: "ACTIVE" | "SUSPENDED" | "PENDING";
  created_at: string;
}

export interface CreateExpertPayload {
  full_name: string;
  email: string;
  phone: string;
  province: string;
}

export interface UpdateExpertPayload {
  full_name?: string;
  email?: string;
  phone?: string;
  province?: string;
}

export function useAdminExperts() {
  const [experts, setExperts] = useState<Expert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const headers = useCallback(() => {
    const token = getTokenFromCookie();
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }, []);

  const fetchExperts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/experts`, {
        headers: headers(),
      });
      if (!res.ok) throw new Error("Uzman listesi yüklenemedi");
      const data = (await res.json()) as { items: Expert[] };
      setExperts(data.items ?? []);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Bir hata oluştu";
      setError(
        msg === "Failed to fetch"
          ? "Sunucuya bağlanılamadı. Lütfen internet bağlantınızı kontrol edin."
          : msg,
      );
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => {
    fetchExperts();
  }, [fetchExperts]);

  const createExpert = useCallback(
    async (payload: CreateExpertPayload) => {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/experts`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          (body as { detail?: string }).detail || "Uzman oluşturulamadı",
        );
      }
      await fetchExperts();
    },
    [headers, fetchExperts],
  );

  const updateExpert = useCallback(
    async (expertId: string, payload: UpdateExpertPayload) => {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/experts/${expertId}`, {
        method: "PATCH",
        headers: headers(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          (body as { detail?: string }).detail || "Uzman güncellenemedi",
        );
      }
      await fetchExperts();
    },
    [headers, fetchExperts],
  );

  const suspendExpert = useCallback(
    async (expertId: string) => {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/experts/${expertId}/suspend`, {
        method: "POST",
        headers: headers(),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(
          (body as { detail?: string }).detail ||
            "Uzman askıya alınamadı",
        );
      }
      await fetchExperts();
    },
    [headers, fetchExperts],
  );

  return {
    experts,
    loading,
    error,
    createExpert,
    updateExpert,
    suspendExpert,
    refreshExperts: fetchExperts,
  };
}
