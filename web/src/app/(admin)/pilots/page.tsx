/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: Pilot kapasite planlama, onay ve atama yonetimi. */
/* KR-015: Gunluk kapasite 2500-3000 donum, calisma gunleri Pzt-Cmt. */

"use client";

import { useState } from "react";

/* ------- Types ------- */
interface Pilot {
  id: string;
  name: string;
  phone: string;
  province: string;
  droneModel: string;
  dailyCapacity: number;
  activeMissions: number;
  status: "Aktif" | "Onay Bekliyor" | "Pasif";
}

const INITIAL_PILOTS: Pilot[] = [
  { id: "p1", name: "Ahmet D.", phone: "0535***1234", province: "Diyarbakir", droneModel: "DJI M3M", dailyCapacity: 3000, activeMissions: 2, status: "Aktif" },
  { id: "p2", name: "Burak K.", phone: "0542***5678", province: "Sanliurfa", droneModel: "WingtraOne", dailyCapacity: 2500, activeMissions: 1, status: "Aktif" },
  { id: "p3", name: "Cem Y.", phone: "0533***9012", province: "Adana", droneModel: "DJI M3M", dailyCapacity: 3000, activeMissions: 0, status: "Aktif" },
  { id: "p4", name: "Deniz A.", phone: "0544***3456", province: "Konya", droneModel: "DJI Mavic 3M", dailyCapacity: 2500, activeMissions: 0, status: "Onay Bekliyor" },
  { id: "p5", name: "Emre S.", phone: "0506***7890", province: "Ankara", droneModel: "MicaSense RedEdge", dailyCapacity: 2800, activeMissions: 0, status: "Onay Bekliyor" },
];

function StatusBadge({ status }: { status: Pilot["status"] }) {
  const cls =
    status === "Aktif"
      ? "bg-emerald-50 text-emerald-700"
      : status === "Onay Bekliyor"
        ? "bg-amber-50 text-amber-700"
        : "bg-slate-100 text-slate-500";
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>;
}

export default function AdminPilotsPage() {
  const [pilots, setPilots] = useState<Pilot[]>(INITIAL_PILOTS);

  const handleApprove = (id: string) => {
    setPilots((prev) => prev.map((p) => (p.id === id ? { ...p, status: "Aktif" as const } : p)));
  };

  const handleReject = (id: string) => {
    setPilots((prev) => prev.filter((p) => p.id !== id));
  };

  const handleDeactivate = (id: string) => {
    setPilots((prev) => prev.map((p) => (p.id === id ? { ...p, status: "Pasif" as const } : p)));
  };

  const activeCount = pilots.filter((p) => p.status === "Aktif").length;
  const pendingCount = pilots.filter((p) => p.status === "Onay Bekliyor").length;
  const totalCapacity = pilots.filter((p) => p.status === "Aktif").reduce((sum, p) => sum + p.dailyCapacity, 0);

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Pilot Yonetimi</h1>
        <p className="mt-0.5 text-sm text-slate-500">
          {activeCount} aktif · {pendingCount} onay bekliyor · Gunluk toplam kapasite: {totalCapacity.toLocaleString("tr-TR")} donum
        </p>
      </div>

      {/* Pending approvals */}
      {pendingCount > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
          <h2 className="mb-3 text-sm font-semibold text-amber-800">Onay Bekleyen Pilotlar ({pendingCount})</h2>
          <div className="space-y-2">
            {pilots.filter((p) => p.status === "Onay Bekliyor").map((p) => (
              <div key={p.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-100 bg-white p-3">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{p.name}</p>
                    <p className="text-xs text-slate-500">{p.phone} · {p.province}</p>
                  </div>
                  <span className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-600">{p.droneModel}</span>
                  <span className="text-xs text-slate-500">{p.dailyCapacity} donum/gun</span>
                </div>
                <div className="flex gap-1.5">
                  <button onClick={() => handleApprove(p.id)} className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700">
                    Onayla
                  </button>
                  <button onClick={() => handleReject(p.id)} className="rounded bg-rose-50 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-100">
                    Reddet
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active / all pilots table */}
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-100 bg-slate-50 px-4 py-2.5">
          <h2 className="text-sm font-semibold text-slate-700">Tum Pilotlar</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="border-b border-slate-100">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Pilot</th>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Bolge</th>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Drone</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">Kapasite (donum/gun)</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">Aktif Gorev</th>
              <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
              <th className="px-4 py-2 text-right font-medium text-slate-600">Islem</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {pilots.map((p) => (
              <tr key={p.id} className="hover:bg-slate-50">
                <td className="px-4 py-2.5">
                  <p className="font-medium text-slate-900">{p.name}</p>
                  <p className="text-xs text-slate-400">{p.phone}</p>
                </td>
                <td className="px-4 py-2.5 text-slate-600">{p.province}</td>
                <td className="px-4 py-2.5">
                  <span className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-xs">{p.droneModel}</span>
                </td>
                <td className="px-4 py-2.5 text-right text-slate-600">{p.dailyCapacity.toLocaleString("tr-TR")}</td>
                <td className="px-4 py-2.5 text-right text-slate-600">{p.activeMissions}</td>
                <td className="px-4 py-2.5"><StatusBadge status={p.status} /></td>
                <td className="px-4 py-2.5 text-right">
                  {p.status === "Aktif" && (
                    <button onClick={() => handleDeactivate(p.id)} className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200">
                      Devre Disi
                    </button>
                  )}
                  {p.status === "Onay Bekliyor" && (
                    <button onClick={() => handleApprove(p.id)} className="rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100">
                      Onayla
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
