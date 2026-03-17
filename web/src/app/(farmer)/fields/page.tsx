/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-013: Tarla kaydi ve yonetimi. */
/* KR-081: Field listesi contract-first tipli render edilir. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getApiBaseUrl } from "@/lib/api";
import { getAuthToken } from "@/lib/authStorage";
import { Button } from "@/components/ui/button";
import { AddFieldModal, type AddFieldPayload } from "@/components/features/field/AddFieldModal";
import { FieldList, type FieldSummary } from "@/components/features/field/FieldList";

interface ApiField {
  field_id: string;
  field_name: string;
  parcel_ref: string;
  area_ha: number;
}

export default function FarmerFieldsPage() {
  const router = useRouter();
  const [fields, setFields] = useState<FieldSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const token = getAuthToken();

  const fetchFields = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/fields`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Tarlalar yüklenemedi");
      const data = (await res.json()) as { items: ApiField[] };
      setFields(
        (data.items ?? []).map((f) => ({
          id: f.field_id,
          name: f.field_name,
          areaHectare: f.area_ha,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchFields();
  }, [fetchFields]);

  const handleAddField = async (payload: AddFieldPayload) => {
    if (!token) return;
    const baseUrl = getApiBaseUrl();
    const parcelRef = `${payload.province}/${payload.district}/${payload.village}/${payload.block}/${payload.parcel}`;
    const areaHa = payload.areaM2 / 10000;

    const res = await fetch(`${baseUrl}/fields`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        field_name: `${payload.province} ${payload.district} ${payload.block}/${payload.parcel}`,
        parcel_ref: parcelRef,
        area_ha: areaHa,
      }),
    });

    if (res.status === 409) {
      throw new Error("Bu ada/parsel zaten kayıtlı.");
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error((body as { detail?: string }).detail || "Tarla eklenemedi");
    }

    await fetchFields();
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tarlalarım</h1>
        <Button onClick={() => setModalOpen(true)}>Tarla Ekle</Button>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yükleniyor...</div>
      ) : (
        <FieldList
          fields={fields}
          onSelectField={(id) => router.push(`/fields/${id}`)}
        />
      )}

      <AddFieldModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleAddField}
      />
    </section>
  );
}
