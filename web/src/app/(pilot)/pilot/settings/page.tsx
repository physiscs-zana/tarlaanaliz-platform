"use client";
import { useState } from "react";
export default function PilotSettingsPage() {
  const [notifyMission, setNotifyMission] = useState(true);
  const [notifyWeather, setNotifyWeather] = useState(true);
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Pilot Ayarlari</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div><p className="text-sm font-medium text-slate-900">Gorev Bildirimleri</p><p className="text-xs text-slate-500">Yeni gorev atandiginda bildirim al</p></div>
          <button onClick={() => setNotifyMission(!notifyMission)} className={`relative h-6 w-11 rounded-full transition ${notifyMission ? "bg-emerald-500" : "bg-slate-300"}`}><span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition ${notifyMission ? "translate-x-5" : ""}`} /></button>
        </div>
        <div className="flex items-center justify-between">
          <div><p className="text-sm font-medium text-slate-900">Hava Durumu Uyarilari</p><p className="text-xs text-slate-500">Ucusa uygun olmayan hava kosullarinda uyari al</p></div>
          <button onClick={() => setNotifyWeather(!notifyWeather)} className={`relative h-6 w-11 rounded-full transition ${notifyWeather ? "bg-emerald-500" : "bg-slate-300"}`}><span className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition ${notifyWeather ? "translate-x-5" : ""}`} /></button>
        </div>
      </div>
    </section>
  );
}
