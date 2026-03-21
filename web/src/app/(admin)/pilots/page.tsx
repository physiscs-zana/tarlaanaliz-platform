/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015: Pilot kapasite planlama, onay ve atama yonetimi. */
/* KR-050: Telefon + 6 haneli PIN ile hesap olusturma. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

/* ------- Types ------- */
interface WeeklyScan {
  field_name: string;
  area_donum: number;
  date: string;
}

interface Pilot {
  userId: string;
  phone: string;
  displayName: string;
  province: string;
  role: string;
  active: boolean;
  weeklyScans: WeeklyScan[];
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
      {active ? "Aktif" : "Pasif"}
    </span>
  );
}

export default function AdminPilotsPage() {
  const [pilots, setPilots] = useState<Pilot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedPilot, setExpandedPilot] = useState<string | null>(null);

  /* Add form state */
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newPin, setNewPin] = useState("");
  const [newProvince, setNewProvince] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  /* Edit province state */
  const [editingPilot, setEditingPilot] = useState<string | null>(null);
  const [editProvince, setEditProvince] = useState("");

  const fetchPilots = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    setLoading(true);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Pilot listesi alinamadi");
      const data = (await res.json()) as Array<{ user_id: string; phone: string; display_name: string; province: string; role: string; active: boolean; weekly_scans?: WeeklyScan[] }>;
      setPilots(data.map((p) => ({
        userId: p.user_id,
        phone: p.phone,
        displayName: p.display_name,
        province: p.province,
        role: p.role,
        active: p.active,
        weeklyScans: p.weekly_scans ?? [],
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hata olustu");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPilots(); }, [fetchPilots]);

  const handleAdd = async () => {
    if (!newName.trim() || !newPhone.trim() || !newPin.trim() || !newProvince.trim()) {
      setAddError("Tum alanlar zorunludur.");
      return;
    }
    if (!/^\d{6}$/.test(newPin)) {
      setAddError("PIN 6 haneli rakam olmalidir.");
      return;
    }
    setAdding(true);
    setAddError(null);
    try {
      const token = getTokenFromCookie();
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          phone: newPhone.trim(),
          pin: newPin,
          display_name: newName.trim(),
          province: newProvince.trim(),
        }),
      });
      if (res.status === 409) { setAddError("Bu telefon numarasi zaten kayitli."); return; }
      if (!res.ok) { setAddError("Pilot eklenemedi."); return; }
      setNewName(""); setNewPhone(""); setNewPin(""); setNewProvince("");
      setShowAddForm(false);
      await fetchPilots();
    } catch {
      setAddError("Baglanti hatasi.");
    } finally {
      setAdding(false);
    }
  };

  const handleUpdateProvince = async (userId: string) => {
    if (!editProvince.trim()) return;
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ province: editProvince.trim() }),
      });
      if (!res.ok) {
        setError("Il guncellenemedi.");
        return;
      }
      setEditingPilot(null);
      setEditProvince("");
      await fetchPilots();
    } catch {
      setError("Baglanti hatasi.");
    }
  };

  const handleDelete = async (userId: string) => {
    if (!confirm("Bu pilotu silmek istediginizden emin misiniz?")) return;
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/pilots/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setError("Pilot silinemedi.");
        return;
      }
      setPilots((prev) => prev.filter((p) => p.userId !== userId));
    } catch {
      setError("Baglanti hatasi.");
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Pilot Yonetimi</h1>
          <p className="mt-0.5 text-sm text-slate-500">{pilots.length} pilot kayitli</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          {showAddForm ? "Iptal" : "Pilot Ekle"}
        </button>
      </div>

      {/* Add pilot form */}
      {showAddForm && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-slate-900">Yeni Pilot Hesabi Olustur</h2>
          <p className="text-xs text-slate-500">Pilota bu telefon ve PIN bilgilerini ileteceksiniz. Pilot bu bilgilerle giris yapacak.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <input placeholder="Ad Soyad" value={newName} onChange={(e) => setNewName(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Telefon (ornek: 05XX...)" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="6 Haneli PIN" type="password" inputMode="numeric" maxLength={6} value={newPin} onChange={(e) => setNewPin(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
            <input placeholder="Il (ornek: Diyarbakir)" value={newProvince} onChange={(e) => setNewProvince(e.target.value)} className="rounded border border-slate-300 px-3 py-2 text-sm" />
          </div>
          {addError && <p className="text-sm text-rose-600">{addError}</p>}
          <button
            onClick={handleAdd}
            disabled={adding}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {adding ? "Olusturuluyor..." : "Pilot Hesabi Olustur"}
          </button>
        </div>
      )}

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : pilots.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          Henuz pilot eklenmemis. Yukaridaki butonla ilk pilotu ekleyin.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Pilot</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Telefon</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Bolge</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Haftalik Tarama</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Islem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {pilots.map((p) => (
                <>
                  <tr key={p.userId} className="hover:bg-slate-50 cursor-pointer" onClick={() => setExpandedPilot(expandedPilot === p.userId ? null : p.userId)}>
                    <td className="px-4 py-2.5">
                      <p className="font-medium text-slate-900">{p.displayName || p.phone}</p>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-slate-700">{p.phone}</td>
                    <td className="px-4 py-2.5 text-slate-600">
                      {editingPilot === p.userId ? (
                        <div className="flex items-center gap-1">
                          <input
                            value={editProvince}
                            onChange={(e) => setEditProvince(e.target.value)}
                            className="w-28 rounded border border-slate-300 px-2 py-1 text-xs"
                            placeholder="Il"
                            onClick={(e) => e.stopPropagation()}
                          />
                          <button onClick={(e) => { e.stopPropagation(); handleUpdateProvince(p.userId); }} className="rounded bg-emerald-50 px-1.5 py-1 text-xs text-emerald-700 hover:bg-emerald-100">&#10003;</button>
                          <button onClick={(e) => { e.stopPropagation(); setEditingPilot(null); }} className="rounded bg-slate-100 px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-200">&#10005;</button>
                        </div>
                      ) : (
                        <span className={p.province ? "" : "text-rose-500 font-medium"}>{p.province || "Belirtilmemis"}</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5"><StatusBadge active={p.active} /></td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">
                      {p.weeklyScans.length > 0
                        ? `${p.weeklyScans.length} tarla taranmis`
                        : "Tarama yok"}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex gap-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); setEditingPilot(p.userId); setEditProvince(p.province); }}
                          className="rounded bg-blue-50 px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-100"
                        >
                          Il
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(p.userId); }}
                          className="rounded bg-rose-50 px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-100"
                        >
                          Sil
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expandedPilot === p.userId && p.weeklyScans.length > 0 && (
                    <tr key={`${p.userId}-detail`}>
                      <td colSpan={6} className="bg-slate-50 px-8 py-3">
                        <p className="mb-2 text-xs font-semibold text-slate-600">Bu Haftaki Taramalar</p>
                        <div className="space-y-1">
                          {p.weeklyScans.map((scan, idx) => (
                            <div key={idx} className="flex items-center gap-4 text-xs text-slate-600">
                              <span className="font-medium">{scan.field_name}</span>
                              <span>{scan.area_donum} donum</span>
                              <span className="text-slate-400">{scan.date}</span>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
