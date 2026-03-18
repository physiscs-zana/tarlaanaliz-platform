/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-013: Tarla detay sayfasi. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface FieldDetail {
  field_id: string;
  field_name: string;
  parcel_ref: string;
  area_ha: number;
  crop_type: string | null;
}

const CROP_LABELS: Record<string, string> = {
  PAMUK: "Pamuk",
  ANTEP_FISTIGI: "Antep Fistigi",
  MISIR: "Misir",
  BUGDAY: "Bugday",
  AYCICEGI: "Aycicegi",
  UZUM: "Uzum",
  ZEYTIN: "Zeytin",
  KIRMIZI_MERCIMEK: "Kirmizi Mercimek",
};

export default function FieldDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [field, setField] = useState<FieldDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchField = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/fields`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as { items: FieldDetail[] };
        const found = data.items?.find((f) => f.field_id === id);
        if (found) setField(found);
      }
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [id]);

  useEffect(() => { fetchField(); }, [fetchField]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  if (!field) {
    return (
      <section className="space-y-4">
        <button onClick={() => router.push("/fields")} className="text-sm text-emerald-600 hover:underline">&larr; Tarlalarim</button>
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">Tarla bulunamadi.</p>
        </div>
      </section>
    );
  }

  const parts = field.parcel_ref.split("/");
  const province = parts[0] || "";
  const district = parts[1] || "";
  const village = parts[2] || "";
  const ada = parts[3] || "";
  const parsel = parts[4] || "";

  return (
    <section className="space-y-6">
      <button onClick={() => router.push("/fields")} className="text-sm text-emerald-600 hover:underline">&larr; Tarlalarim</button>

      <div>
        <h1 className="text-2xl font-semibold">{field.field_name}</h1>
        <p className="mt-0.5 text-sm text-slate-500">{field.parcel_ref}</p>
      </div>

      {/* Tarla Bilgileri */}
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-600">Tarla Bilgileri</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-xs text-slate-400">Il</p>
            <p className="font-medium text-slate-900">{province}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Ilce</p>
            <p className="font-medium text-slate-900">{district}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Mahalle / Koy</p>
            <p className="font-medium text-slate-900">{village}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Ada / Parsel</p>
            <p className="font-medium text-slate-900">{ada} / {parsel}</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Alan</p>
            <p className="font-medium text-slate-900">{(field.area_ha * 10).toFixed(1)} donum ({field.area_ha.toFixed(2)} ha)</p>
          </div>
          <div>
            <p className="text-xs text-slate-400">Bitki Turu</p>
            <p className="font-medium text-slate-900">{field.crop_type ? (CROP_LABELS[field.crop_type] ?? field.crop_type) : "Belirtilmemis"}</p>
          </div>
        </div>
      </div>

      {/* Harita Placeholder */}
      <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <div className="text-4xl text-slate-300">&#128506;</div>
        <p className="mt-2 text-lg font-medium text-slate-500">Harita Gorunumu</p>
        <p className="mt-1 text-sm text-slate-400">Tarla sinir haritasi yakinda aktif olacaktir.</p>
      </div>

      {/* Analiz Sonuclari Placeholder */}
      <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
        <div className="text-4xl text-slate-300">&#128202;</div>
        <p className="mt-2 text-lg font-medium text-slate-500">Analiz Sonuclari</p>
        <p className="mt-1 text-sm text-slate-400">Drone taramasi yapildiktan sonra analiz sonuclari burada gorunecektir.</p>
      </div>
    </section>
  );
}
