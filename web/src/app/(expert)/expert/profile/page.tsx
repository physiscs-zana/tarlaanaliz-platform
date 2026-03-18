/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-050: Uzman profili ve PIN degistirme. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie, decodeJwtPayload } from "@/lib/api";

interface ExpertiseItem {
  crop: string;
  layer: string;
}

const CROP_LABELS: Record<string, string> = {
  PAMUK: "Pamuk", ANTEP_FISTIGI: "Antep Fistigi", MISIR: "Misir", BUGDAY: "Bugday",
  AYCICEGI: "Aycicegi", UZUM: "Uzum", ZEYTIN: "Zeytin", KIRMIZI_MERCIMEK: "Kirmizi Mercimek",
};
const LAYER_LABELS: Record<string, string> = {
  DISEASE: "Hastalik", PEST: "Zararli Bocek", WEED: "Yabanci Ot",
  WATER_STRESS: "Su Stresi", N_STRESS: "Azot Stresi", THERMAL_STRESS: "Termal Stres",
};

function parseExpertiseTags(tags: string[]): ExpertiseItem[] {
  return tags
    .map((tag) => { const [crop, layer] = tag.split(":"); return crop && layer ? { crop, layer } : null; })
    .filter((c): c is ExpertiseItem => c !== null);
}

function groupByCrop(items: ExpertiseItem[]): Record<string, string[]> {
  const map: Record<string, string[]> = {};
  for (const item of items) {
    if (!map[item.crop]) map[item.crop] = [];
    map[item.crop].push(item.layer);
  }
  return map;
}

export default function ExpertProfilePage() {
  const [phone, setPhone] = useState("");
  const [userId, setUserId] = useState("");
  const [expertise, setExpertise] = useState<ExpertiseItem[]>([]);
  const [expertiseLoading, setExpertiseLoading] = useState(true);
  const [showPinChange, setShowPinChange] = useState(false);
  const [currentPin, setCurrentPin] = useState("");
  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [pinError, setPinError] = useState<string | null>(null);
  const [pinSuccess, setPinSuccess] = useState(false);
  const [pinLoading, setPinLoading] = useState(false);

  useEffect(() => {
    const token = getTokenFromCookie();
    if (!token) return;
    const claims = decodeJwtPayload(token);
    setPhone((claims.phone as string) ?? "");
    setUserId((claims.user_id as string) ?? "");
  }, []);

  const fetchExpertise = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setExpertiseLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/expert-portal/me/expertise`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) { setExpertiseLoading(false); return; }
      const data = (await res.json()) as { expertise_tags: string[] };
      setExpertise(parseExpertiseTags(data.expertise_tags ?? []));
    } catch { /* ignore */ } finally { setExpertiseLoading(false); }
  }, []);

  useEffect(() => { fetchExpertise(); }, [fetchExpertise]);

  const maskPhone = (p: string) => (p.length < 4 ? p : p.slice(0, -4).replace(/./g, "*") + p.slice(-4));

  const handlePinChange = async () => {
    setPinError(null);
    setPinSuccess(false);
    if (!/^\d{6}$/.test(currentPin)) { setPinError("Mevcut PIN 6 haneli sayi olmalidir."); return; }
    if (!/^\d{6}$/.test(newPin)) { setPinError("Yeni PIN 6 haneli sayi olmalidir."); return; }
    if (newPin !== confirmPin) { setPinError("Yeni PIN ve tekrari eslesmiyor."); return; }
    if (currentPin === newPin) { setPinError("Yeni PIN mevcut PIN'den farkli olmalidir."); return; }

    setPinLoading(true);
    try {
      const token = getTokenFromCookie();
      if (!token) { setPinError("Oturum bulunamadi."); return; }
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/auth/phone-pin/change-pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_pin: currentPin, new_pin: newPin }),
      });
      if (res.status === 401) { setPinError("Mevcut PIN hatali."); return; }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setPinError((body as { detail?: string }).detail || "PIN degistirilemedi.");
        return;
      }
      setPinSuccess(true);
      setCurrentPin(""); setNewPin(""); setConfirmPin("");
      setTimeout(() => { setShowPinChange(false); setPinSuccess(false); }, 2000);
    } catch { setPinError("Bir hata olustu."); } finally { setPinLoading(false); }
  };

  if (!phone) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  const grouped = groupByCrop(expertise);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Uzman Profili</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <div><span className="text-sm text-slate-500">Telefon</span><p className="text-base font-medium text-slate-900">{maskPhone(phone)}</p></div>
        <div><span className="text-sm text-slate-500">Rol</span><p className="text-base font-medium text-slate-900">Uzman</p></div>
        <div><span className="text-sm text-slate-500">Kullanici ID</span><p className="font-mono text-xs text-slate-400">{userId}</p></div>
      </div>

      {/* KR-019: Uzmanlik alanlari — backend'den gelen veriler */}
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <h2 className="text-lg font-semibold">Uzmanlik Alanlari</h2>
        <p className="text-xs text-slate-500">Inceleme kuyrugunuzda asagidaki bitki ve durum kombinasyonlari onceliklendirilir.</p>
        {expertiseLoading ? (
          <div className="py-4 text-center text-sm text-slate-500">Yukleniyor...</div>
        ) : expertise.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-8 text-center">
            <p className="text-sm font-medium text-slate-500">HENÜZ VERİ-BİLGİ BULUNMAMAKTADIR</p>
            <p className="mt-1 text-xs text-slate-400">Uzmanlik alanlariniz admin tarafindan atanmamistir.</p>
          </div>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(grouped).map(([crop, layers]) => (
              <div key={crop} className="rounded border border-slate-100 p-3">
                <p className="text-sm font-medium text-slate-900">{CROP_LABELS[crop] ?? crop}</p>
                <p className="text-xs text-slate-500">{layers.map((l) => LAYER_LABELS[l] ?? l).join(", ")}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        {!showPinChange ? (
          <button onClick={() => setShowPinChange(true)} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">Sifre (PIN) Degistir</button>
        ) : (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">PIN Degistir</h2>
            <p className="text-xs text-slate-500">PIN 6 haneli sayisal olmalidir.</p>
            <input type="password" inputMode="numeric" maxLength={6} placeholder="Mevcut PIN" value={currentPin} onChange={(e) => setCurrentPin(e.target.value.replace(/\D/g, "").slice(0, 6))} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
            <input type="password" inputMode="numeric" maxLength={6} placeholder="Yeni PIN" value={newPin} onChange={(e) => setNewPin(e.target.value.replace(/\D/g, "").slice(0, 6))} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
            <input type="password" inputMode="numeric" maxLength={6} placeholder="Yeni PIN (Tekrar)" value={confirmPin} onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, "").slice(0, 6))} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
            {pinError && <p className="text-sm text-rose-600">{pinError}</p>}
            {pinSuccess && <p className="text-sm text-emerald-600">PIN basariyla degistirildi!</p>}
            <div className="flex gap-2">
              <button onClick={handlePinChange} disabled={pinLoading} className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50">{pinLoading ? "Degistiriliyor..." : "Degistir"}</button>
              <button onClick={() => { setShowPinChange(false); setPinError(null); setCurrentPin(""); setNewPin(""); setConfirmPin(""); }} className="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">Iptal</button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
