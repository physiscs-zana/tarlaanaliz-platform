/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif tarla yonetimi — uyelerin tarlalarini listeler. */
/* KR-013: Tarla benzersizligi: il+ilce+mahalle+ada+parsel. "Tarla kaydi tekil, sahiplik/erisim ayri." */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface CoopField {
  readonly field_id: string;
  readonly owner_name: string;
  readonly province: string;
  readonly district: string;
  readonly village: string;
  readonly block_no: string;
  readonly parcel_no: string;
  readonly area_donum: number;
  readonly crop_type: string | null;
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

export default function CoopFieldsPage() {
  const [fields, setFields] = useState<readonly CoopField[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFields = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/coop/fields`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as CoopField[];
        setFields(data ?? []);
      }
    } catch { /* noop */ }
    setLoading(false);
  }, []);

  useEffect(() => { fetchFields(); }, [fetchFields]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Kooperatif Tarlalari</h1>
      <p className="text-sm text-slate-500">
        Kooperatif uyelerine ait tarlalar. Tarla kaydi tekil olup sahiplik ve erisim ayri yonetilir.
      </p>

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : fields.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
          <p className="text-sm text-slate-500">Henuz kooperatif tarlasi bulunmuyor.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Sahip</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Il / Ilce</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Koy</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Ada / Parsel</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Alan (donum)</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Bitki</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {fields.map((f) => (
                <tr key={f.field_id} className="hover:bg-slate-50">
                  <td className="px-3 py-2 text-slate-800">{f.owner_name}</td>
                  <td className="px-3 py-2 text-slate-600">{f.province} / {f.district}</td>
                  <td className="px-3 py-2 text-slate-600">{f.village}</td>
                  <td className="px-3 py-2 text-slate-600 font-mono text-xs">{f.block_no} / {f.parcel_no}</td>
                  <td className="px-3 py-2 text-slate-700 font-medium">{f.area_donum.toFixed(1)}</td>
                  <td className="px-3 py-2 text-slate-600">{f.crop_type ? (CROP_LABELS[f.crop_type] ?? f.crop_type) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
