/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: Fiyat yonetimi — IBAN + bitki turune gore fiyat belirleme. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface CropPrice {
  code: string;
  label: string;
  single_price: number;
  seasonal_price: number;
  interval_days: number;
}

interface PricingConfig {
  iban: string;
  bank_name: string;
  recipient: string;
  crops: CropPrice[];
  last_updated?: string;
}

const DEFAULT_CONFIG: PricingConfig = {
  iban: "TR33 0006 1005 1978 6457 8413 26",
  bank_name: "Halkbank",
  recipient: "TarlaAnaliz Tarim Teknolojileri A.S.",
  crops: [
    { code: "PAMUK", label: "Pamuk", single_price: 250, seasonal_price: 120, interval_days: 7 },
    { code: "ANTEP_FISTIGI", label: "Antep Fistigi", single_price: 250, seasonal_price: 120, interval_days: 10 },
    { code: "MISIR", label: "Misir", single_price: 250, seasonal_price: 120, interval_days: 15 },
    { code: "BUGDAY", label: "Bugday", single_price: 250, seasonal_price: 120, interval_days: 10 },
    { code: "AYCICEGI", label: "Aycicegi", single_price: 250, seasonal_price: 120, interval_days: 7 },
    { code: "UZUM", label: "Uzum", single_price: 250, seasonal_price: 120, interval_days: 7 },
    { code: "ZEYTIN", label: "Zeytin", single_price: 250, seasonal_price: 120, interval_days: 15 },
    { code: "KIRMIZI_MERCIMEK", label: "Kirmizi Mercimek", single_price: 250, seasonal_price: 120, interval_days: 10 },
  ],
};

export default function PriceManagementPage() {
  const [config, setConfig] = useState<PricingConfig>(DEFAULT_CONFIG);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const fetchConfig = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/pricing/config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as PricingConfig;
        if (data.crops && data.crops.length > 0) setConfig(data);
      }
    } catch { /* use defaults */ }
  }, []);

  useEffect(() => { fetchConfig(); }, [fetchConfig]);

  const handleSave = async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    setSaving(true);
    setMessage(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/pricing/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(config),
      });
      if (res.ok) {
        await fetchConfig();
        setMessage({ type: "ok", text: "Ayarlar kaydedildi. Degisiklikler ciftci sayfalarinda gorunur." });
        setTimeout(() => setMessage(null), 5000);
      } else {
        setMessage({ type: "err", text: "Kaydedilemedi." });
      }
    } catch {
      setMessage({ type: "err", text: "Baglanti hatasi." });
    } finally {
      setSaving(false);
    }
  };

  const updateCrop = (code: string, field: keyof CropPrice, value: number) => {
    setConfig((prev) => ({
      ...prev,
      crops: prev.crops.map((c) => (c.code === code ? { ...c, [field]: value } : c)),
    }));
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Fiyat ve Odeme Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">IBAN bilgileri ve bitki turune gore analiz fiyatlarini belirleyin.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {saving ? "Kaydediliyor..." : "Tum Ayarlari Kaydet"}
        </button>
        {config.last_updated && (
          <p className="text-xs text-slate-400">
            Son guncelleme: {new Date(config.last_updated).toLocaleString("tr-TR")}
          </p>
        )}
      </div>

      {message && (
        <div className={`rounded-lg border p-3 text-sm ${message.type === "ok" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-rose-200 bg-rose-50 text-rose-700"}`}>
          {message.text}
        </div>
      )}

      {/* ===== IBAN / Odeme Bilgileri ===== */}
      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-5 space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Havale / EFT Bilgileri</h2>
        <p className="text-xs text-slate-500">Bu bilgiler ciftcilerin odeme sayfasinda gorunur.</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">IBAN</label>
            <input
              value={config.iban}
              onChange={(e) => setConfig((p) => ({ ...p, iban: e.target.value }))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm font-mono"
              placeholder="TR..."
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Banka</label>
            <input
              value={config.bank_name}
              onChange={(e) => setConfig((p) => ({ ...p, bank_name: e.target.value }))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Alici Adi</label>
            <input
              value={config.recipient}
              onChange={(e) => setConfig((p) => ({ ...p, recipient: e.target.value }))}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
      </div>

      {/* ===== Bitki Fiyatlari ===== */}
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100 bg-slate-50">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium text-slate-600">Bitki Turu</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Tek Seferlik (TL/ha)</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Sezonluk (TL/ha)</th>
              <th className="px-4 py-2.5 text-right font-medium text-slate-600">Tarama Periyodu (gun)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {config.crops.map((c) => (
              <tr key={c.code} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{c.label}</td>
                <td className="px-4 py-3 text-right">
                  <input type="number" min={0} step={10} value={c.single_price} onChange={(e) => updateCrop(c.code, "single_price", Number(e.target.value))} className="w-24 rounded border border-slate-300 px-2 py-1 text-right text-sm" />
                </td>
                <td className="px-4 py-3 text-right">
                  <input type="number" min={0} step={10} value={c.seasonal_price} onChange={(e) => updateCrop(c.code, "seasonal_price", Number(e.target.value))} className="w-24 rounded border border-slate-300 px-2 py-1 text-right text-sm" />
                </td>
                <td className="px-4 py-3 text-right">
                  <input type="number" min={1} max={30} value={c.interval_days} onChange={(e) => updateCrop(c.code, "interval_days", Number(e.target.value))} className="w-20 rounded border border-slate-300 px-2 py-1 text-right text-sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400">
        Kaydet butonuna bastiginizda IBAN ve fiyat bilgileri aninda guncellenir. Ciftciler odeme sayfasinda yeni IBAN bilgilerini gorur.
      </p>
    </section>
  );
}
