/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-013: Tarla detay + analiz talebi olusturma. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface FieldDetail {
  field_id: string;
  field_code: string;
  field_name: string;
  parcel_ref: string;
  area_ha: number;
  crop_type: string | null;
}

interface CropPrice {
  code: string;
  label: string;
  single_price: number;
  seasonal_price: number;
  interval_days: number;
}

const CROP_LABELS: Record<string, string> = {
  PAMUK: "Pamuk", ANTEP_FISTIGI: "Antep Fistigi", MISIR: "Misir", BUGDAY: "Bugday",
  AYCICEGI: "Aycicegi", UZUM: "Uzum", ZEYTIN: "Zeytin", KIRMIZI_MERCIMEK: "Kirmizi Mercimek",
};

export default function FieldDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [field, setField] = useState<FieldDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [cropPrices, setCropPrices] = useState<CropPrice[]>([]);
  const [planType, setPlanType] = useState<"single" | "seasonal">("single");
  const [seasonWeeks, setSeasonWeeks] = useState(12);
  const [scanInterval, setScanInterval] = useState(10);
  const [requestSent, setRequestSent] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [priceError, setPriceError] = useState(false);

  const fetchField = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/fields`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = (await res.json()) as { items: FieldDetail[] };
        const found = data.items?.find((f) => f.field_id === id);
        if (found) setField(found);
      }
    } catch { /* ignore */ } finally { setLoading(false); }
  }, [id]);

  const fetchPrices = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pricing/crops`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (!res.ok) {
        setPriceError(true);
        return;
      }
      const data = (await res.json()) as { crops: CropPrice[] };
      const crops = data.crops ?? [];
      if (crops.length === 0) {
        setPriceError(true);
        return;
      }
      setCropPrices(crops);
      setPriceError(false);
    } catch {
      setPriceError(true);
    }
  }, []);

  useEffect(() => { fetchField(); fetchPrices(); }, [fetchField, fetchPrices]);

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

  // Price calculation — per 10m² precision (1 ha = 10000 m², 1 unit = 10 m²)
  const cropPrice = cropPrices.find((c) => c.code === field.crop_type);
  const priceReady = cropPrices.length > 0 && cropPrice != null;
  const areaHa = field.area_ha;
  const areaM2 = areaHa * 10000;
  const totalScans = planType === "single" ? 1 : Math.max(1, Math.floor((seasonWeeks * 7) / scanInterval));
  const pricePerHa = priceReady
    ? (planType === "single" ? cropPrice.single_price : cropPrice.seasonal_price)
    : 0;
  // Calculate per 10m² then round to nearest lira
  const pricePerM2 = pricePerHa / 10000;
  const unitArea = Math.ceil(areaM2 / 10) * 10; // round up to nearest 10 m²
  const totalPrice = Math.round(unitArea * pricePerM2 * (planType === "seasonal" ? totalScans : 1));

  const handleRequest = async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    setSubmitting(true);
    setRequestError(null);
    try {
      const baseUrl = getApiBaseUrl();
      if (planType === "single") {
        const res = await fetch(`${baseUrl}/missions`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            field_id: field.field_id,
            mission_date: new Date().toISOString().split("T")[0],
            crop_type: field.crop_type || "PAMUK",
            analysis_type: "FULL",
          }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error((body as { detail?: string }).detail || "Talep olusturulamadi");
        }
      } else {
        const startDate = new Date();
        const endDate = new Date();
        endDate.setDate(endDate.getDate() + seasonWeeks * 7);
        const res = await fetch(`${baseUrl}/subscriptions`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            field_id: field.field_id,
            crop_type: field.crop_type || "PAMUK",
            start_date: startDate.toISOString().split("T")[0],
            end_date: endDate.toISOString().split("T")[0],
            interval_days: scanInterval,
            plan_code: "SEASONAL",
          }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error((body as { detail?: string }).detail || "Talep olusturulamadi");
        }
      }
      setRequestSent(true);
    } catch (err) {
      setRequestError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setSubmitting(false);
    }
  };

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
          <div><p className="text-xs text-slate-400">Tarla Kodu</p><p className="font-medium text-slate-900">{field.field_code}</p></div>
          <div><p className="text-xs text-slate-400">Il</p><p className="font-medium text-slate-900">{province}</p></div>
          <div><p className="text-xs text-slate-400">Ilce</p><p className="font-medium text-slate-900">{district}</p></div>
          <div><p className="text-xs text-slate-400">Mahalle / Koy</p><p className="font-medium text-slate-900">{village}</p></div>
          <div><p className="text-xs text-slate-400">Ada / Parsel</p><p className="font-medium text-slate-900">{ada} / {parsel}</p></div>
          <div><p className="text-xs text-slate-400">Alan</p><p className="font-medium text-slate-900">{(areaHa * 10).toFixed(1)} donum ({areaHa.toFixed(2)} ha)</p></div>
          <div><p className="text-xs text-slate-400">Bitki Turu</p><p className="font-medium text-slate-900">{field.crop_type ? (CROP_LABELS[field.crop_type] ?? field.crop_type) : "Belirtilmemis"}</p></div>
        </div>
      </div>

      {/* Analiz Talebi */}
      {requestSent ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 text-center space-y-2">
          <div className="text-3xl">&#9989;</div>
          <p className="text-lg font-semibold text-emerald-800">Analiz Talebiniz Olusturuldu</p>
          <p className="text-sm text-emerald-600">
            {planType === "single" ? "Tek seferlik analiz talebi kaydedildi." : `${totalScans} taramadan olusan sezonluk paket olusturuldu.`}
            {" "}Odeme sayfasindan odemenizi tamamlayabilirsiniz.
          </p>
          <div className="flex justify-center gap-3 mt-3">
            <button onClick={() => router.push("/payments")} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">Odeme Yap</button>
            <button onClick={() => router.push("/fields")} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">Tarlalarim</button>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-5 space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Analiz Talebi Olustur</h2>

          {/* Plan secimi */}
          <div className="flex gap-3">
            <button
              onClick={() => setPlanType("single")}
              className={`flex-1 rounded-lg border-2 p-3 text-center transition ${planType === "single" ? "border-emerald-600 bg-emerald-50" : "border-slate-200 bg-white"}`}
            >
              <p className="font-semibold text-slate-900">Tek Seferlik</p>
              <p className="text-xs text-slate-500">Bir kez tarama + analiz</p>
            </button>
            <button
              onClick={() => setPlanType("seasonal")}
              className={`flex-1 rounded-lg border-2 p-3 text-center transition ${planType === "seasonal" ? "border-emerald-600 bg-emerald-50" : "border-slate-200 bg-white"}`}
            >
              <p className="font-semibold text-slate-900">Sezonluk Paket</p>
              <p className="text-xs text-slate-500">D&uuml;zenli Tarama + Analiz</p>
            </button>
          </div>

          {/* Sezonluk ayarlar */}
          {planType === "seasonal" && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Tarama Sikligi (kac gunde bir)</label>
                <select value={scanInterval} onChange={(e) => setScanInterval(Number(e.target.value))} className="w-full rounded border border-slate-300 px-3 py-2 text-sm">
                  <option value={7}>Her 7 gunde bir (haftalik)</option>
                  <option value={10}>Her 10 gunde bir</option>
                  <option value={14}>Her 14 gunde bir (2 haftada bir)</option>
                  <option value={17}>Her 17 gunde bir</option>
                  <option value={21}>Her 21 gunde bir (3 haftada bir)</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Sezon Suresi (hafta)</label>
                <input type="number" min={4} max={52} value={seasonWeeks} onChange={(e) => setSeasonWeeks(Number(e.target.value))} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
              </div>
              <p className="sm:col-span-2 text-xs text-slate-400">Her {scanInterval} gunde bir tarama yapilir. Toplam {totalScans} tarama.</p>
            </div>
          )}

          {/* Fiyat uyarilari */}
          {!priceReady && !priceError && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              {!field.crop_type
                ? "Bu tarla icin bitki turu belirtilmemis. Fiyat hesaplanamaz."
                : "Bu bitki turu icin fiyat bilgisi bulunamadi."}
            </div>
          )}
          {priceError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              Fiyat bilgisi alinamadi. Lutfen sayfayi yenileyin.
            </div>
          )}

          {/* Fiyat hesabi */}
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">
                  {(unitArea / 10000).toFixed(2)} ha ({unitArea.toLocaleString("tr-TR")} m&sup2;) &times; {pricePerHa} TL/ha
                  {planType === "seasonal" ? ` × ${totalScans} tarama` : ""}
                </p>
                <p className="text-xs text-slate-400">
                  {field.crop_type ? (CROP_LABELS[field.crop_type] ?? field.crop_type) : ""} &mdash; {planType === "single" ? "tek seferlik" : "sezonluk"} fiyat
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-emerald-700">{totalPrice.toLocaleString("tr-TR")} TL</p>
                <p className="text-xs text-slate-400">KDV dahil</p>
              </div>
            </div>
          </div>

          {requestError && <p className="text-sm text-rose-600">{requestError}</p>}

          <button
            onClick={handleRequest}
            disabled={submitting || !priceReady || priceError}
            className="w-full rounded-lg bg-emerald-600 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {submitting ? "Olusturuluyor..." : `Analiz Talebi Olustur — ${totalPrice.toLocaleString("tr-TR")} TL`}
          </button>
        </div>
      )}

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
