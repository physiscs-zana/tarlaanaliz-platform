"use client";
import { useEffect, useState } from "react";
import { getTokenFromCookie, decodeJwtPayload } from "@/lib/api";
export default function PilotProfilePage() {
  const [phone, setPhone] = useState("");
  const [droneModel, setDroneModel] = useState("");
  const [droneSerial, setDroneSerial] = useState("");
  const [sensorType, setSensorType] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    const token = getTokenFromCookie();
    if (!token) return;
    const claims = decodeJwtPayload(token);
    setPhone((claims.phone as string) ?? "");
  }, []);
  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000); };
  const maskPhone = (p: string) => p.length < 4 ? p : p.slice(0, -4).replace(/./g, "*") + p.slice(-4);
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Pilot Profili</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
        <div><span className="text-sm text-slate-500">Telefon</span><p className="text-base font-medium">{maskPhone(phone)}</p></div>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
        <h2 className="text-lg font-semibold">Drone Bilgileri</h2>
        <p className="text-xs text-slate-500">Sahip oldugunuz drone bilgilerini girin. Bu bilgiler gorev atamasinda kullanilir.</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div><label className="mb-1 block text-sm font-medium">Drone Modeli</label><select value={droneModel} onChange={(e) => setDroneModel(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm"><option value="">Secin</option><option value="DJI M3M">DJI Matrice 300 RTK + MicaSense</option><option value="DJI Mavic 3M">DJI Mavic 3 Multispectral</option><option value="WingtraOne">WingtraOne Gen II</option><option value="senseFly eBee X">senseFly eBee X + Sequoia</option><option value="Diger">Diger</option></select></div>
          <div><label className="mb-1 block text-sm font-medium">Seri Numarasi</label><input placeholder="ornek: 1ZNBJ1234567" value={droneSerial} onChange={(e) => setDroneSerial(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" /></div>
        </div>
        <div><label className="mb-1 block text-sm font-medium">Sensor Tipi</label><select value={sensorType} onChange={(e) => setSensorType(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2 text-sm"><option value="">Secin</option><option value="MicaSense RedEdge-MX">MicaSense RedEdge-MX (5 bant)</option><option value="MicaSense Altum-PT">MicaSense Altum-PT (6 bant + termal)</option><option value="DJI Multispectral">DJI Multispectral (4 bant)</option><option value="Sequoia+">Parrot Sequoia+ (4 bant)</option></select></div>
        {saved && <p className="text-sm text-emerald-600">Bilgiler kaydedildi.</p>}
        <button onClick={handleSave} disabled={!droneModel} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50">Kaydet</button>
      </div>
    </section>
  );
}
