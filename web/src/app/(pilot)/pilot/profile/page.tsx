/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-050: Pilot profili ve PIN degistirme. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie, decodeJwtPayload } from "@/lib/api";

export default function PilotProfilePage() {
  const [phone, setPhone] = useState("");
  const [droneModel, setDroneModel] = useState("");
  const [droneSerial, setDroneSerial] = useState("");
  const [sensorType, setSensorType] = useState("");
  const [saved, setSaved] = useState(false);
  const [droneLocked, setDroneLocked] = useState(false);
  const [droneLoading, setDroneLoading] = useState(true);
  const [droneError, setDroneError] = useState<string | null>(null);

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
  }, []);

  const fetchDroneInfo = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setDroneLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/me/drone`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as { drone_model?: string; drone_serial?: string; sensor_type?: string; locked?: boolean };
        if (data.drone_model) {
          setDroneModel(data.drone_model);
          setDroneSerial(data.drone_serial ?? "");
          setSensorType(data.sensor_type ?? "");
          setDroneLocked(data.locked ?? true);
        }
      }
    } catch { /* ignore */ } finally { setDroneLoading(false); }
  }, []);

  useEffect(() => { fetchDroneInfo(); }, [fetchDroneInfo]);

  const handleSave = async () => {
    if (droneLocked) return;
    setDroneError(null);
    if (!droneModel) { setDroneError("Drone modeli secilmelidir."); return; }

    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/me/drone`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ drone_model: droneModel, drone_serial: droneSerial, sensor_type: sensorType }),
      });
      if (res.ok) {
        setSaved(true);
        setDroneLocked(true);
        setTimeout(() => setSaved(false), 2000);
      } else {
        const body = await res.json().catch(() => ({}));
        setDroneError((body as { detail?: string }).detail || "Bilgiler kaydedilemedi.");
      }
    } catch { setDroneError("Baglanti hatasi."); }
  };

  const maskPhone = (p: string) => p.length < 4 ? p : p.slice(0, -4).replace(/./g, "*") + p.slice(-4);

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

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Pilot Profili</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <div><span className="text-sm text-slate-500">Telefon</span><p className="text-base font-medium">{maskPhone(phone)}</p></div>
      </div>

      {/* Drone Bilgileri */}
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
        <h2 className="text-lg font-semibold">Drone Bilgileri</h2>
        <p className="text-xs text-slate-500">Sahip oldugunuz drone bilgilerini girin. Bu bilgiler gorev atamasinda kullanilir.</p>

        {droneLocked && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            <strong>Uyari:</strong> Drone bilgileri yalnizca bir kez girilip kaydedilebilir. Degisiklik icin Central Admin onayi gereklidir.
            Degisiklik talep etmek icin yoneticinize basvurunuz.
          </div>
        )}

        {droneLoading ? (
          <div className="py-4 text-center text-sm text-slate-500">Yukleniyor...</div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium">Drone Modeli</label>
                <select value={droneModel} onChange={(e) => setDroneModel(e.target.value)} disabled={droneLocked} className={`w-full rounded border border-slate-300 px-3 py-2 text-sm ${droneLocked ? "opacity-60 cursor-not-allowed bg-slate-100" : ""}`}>
                  <option value="">Secin</option>
                  <option value="DJI M3M">DJI Matrice 300 RTK + MicaSense</option>
                  <option value="DJI Mavic 3M">DJI Mavic 3 Multispectral</option>
                  <option value="WingtraOne">WingtraOne Gen II</option>
                  <option value="senseFly eBee X">senseFly eBee X + Sequoia</option>
                  <option value="Diger">Diger</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Seri Numarasi</label>
                <input placeholder="ornek: 1ZNBJ1234567" value={droneSerial} onChange={(e) => setDroneSerial(e.target.value)} disabled={droneLocked} className={`w-full rounded border border-slate-300 px-3 py-2 text-sm ${droneLocked ? "opacity-60 cursor-not-allowed bg-slate-100" : ""}`} />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Sensor Tipi</label>
              <select value={sensorType} onChange={(e) => setSensorType(e.target.value)} disabled={droneLocked} className={`w-full rounded border border-slate-300 px-3 py-2 text-sm ${droneLocked ? "opacity-60 cursor-not-allowed bg-slate-100" : ""}`}>
                <option value="">Secin</option>
                <option value="MicaSense RedEdge-MX">MicaSense RedEdge-MX (5 bant)</option>
                <option value="MicaSense Altum-PT">MicaSense Altum-PT (6 bant + termal)</option>
                <option value="DJI Multispectral">DJI Multispectral (4 bant)</option>
                <option value="Sequoia+">Parrot Sequoia+ (4 bant)</option>
              </select>
            </div>
            {droneError && <p className="text-sm text-rose-600">{droneError}</p>}
            {saved && <p className="text-sm text-emerald-600">Bilgiler kaydedildi.</p>}
            {!droneLocked && (
              <button onClick={handleSave} disabled={!droneModel} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50">Kaydet</button>
            )}
          </>
        )}
      </div>

      {/* PIN Degistir */}
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
