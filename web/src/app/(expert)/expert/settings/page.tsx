/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-019: Uzman portal ayarlari. */

"use client";

import { useState } from "react";

export default function ExpertSettingsPage() {
  const [notifSound, setNotifSound] = useState(true);
  const [defaultBand, setDefaultBand] = useState("NDVI");
  const [autoAccept, setAutoAccept] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Ayarlar</h1>

      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-5">
        {/* Bildirim Sesi */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-900">Bildirim Sesi</p>
            <p className="text-xs text-slate-500">Yeni inceleme geldiginde sesli bildirim</p>
          </div>
          <button
            onClick={() => setNotifSound(!notifSound)}
            className={`relative h-6 w-11 rounded-full transition-colors ${notifSound ? "bg-emerald-500" : "bg-slate-300"}`}
          >
            <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${notifSound ? "left-[22px]" : "left-0.5"}`} />
          </button>
        </div>

        {/* Varsayilan Bant */}
        <div>
          <p className="text-sm font-medium text-slate-900">Varsayilan Bant Gorunumu</p>
          <p className="mb-2 text-xs text-slate-500">Inceleme ekraninda ilk acilan bant katmani</p>
          <select
            value={defaultBand}
            onChange={(e) => setDefaultBand(e.target.value)}
            className="rounded border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="NDVI">NDVI (Bitki Sagligi)</option>
            <option value="NDRE">NDRE (Azot Durumu)</option>
            <option value="GNDVI">GNDVI (Klorofil)</option>
            <option value="EVI">EVI (Yogun Bitki Ortumu)</option>
            <option value="THERMAL">Termal (Sicaklik)</option>
          </select>
        </div>

        {/* Otomatik Kabul */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-900">Dusuk Oncelikli Otomatik Kabul</p>
            <p className="text-xs text-slate-500">Dusuk oncelikli incelemeleri otomatik kabul et</p>
          </div>
          <button
            onClick={() => setAutoAccept(!autoAccept)}
            className={`relative h-6 w-11 rounded-full transition-colors ${autoAccept ? "bg-emerald-500" : "bg-slate-300"}`}
          >
            <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${autoAccept ? "left-[22px]" : "left-0.5"}`} />
          </button>
        </div>
      </div>

      {saved && <p className="text-sm text-emerald-600">Ayarlar kaydedildi.</p>}
      <button
        onClick={handleSave}
        className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
      >
        Kaydet
      </button>
    </section>
  );
}
