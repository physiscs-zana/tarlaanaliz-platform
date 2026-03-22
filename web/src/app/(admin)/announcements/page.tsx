/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-012: Admin duyuru yonetimi — olustur, listele, devre disi birak. */

"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface Announcement {
  announcement_id: string;
  announcement_type: string;
  title: string;
  body: string;
  target_date: string | null;
  target_province: string | null;
  visible_from: string;
  visible_until: string | null;
  created_at: string;
}

const TYPES = [
  { value: "FLIGHT_START", label: "Ucus Baslangic Tarihi" },
  { value: "CAMPAIGN", label: "Kampanya / Indirim" },
  { value: "GENERAL", label: "Genel Bilgilendirme" },
  { value: "MAINTENANCE", label: "Sistem Bakimi" },
];

const TYPE_BADGE: Record<string, string> = {
  FLIGHT_START: "bg-emerald-100 text-emerald-800",
  CAMPAIGN: "bg-amber-100 text-amber-800",
  GENERAL: "bg-blue-100 text-blue-800",
  MAINTENANCE: "bg-red-100 text-red-800",
};

export default function AnnouncementsAdminPage() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formType, setFormType] = useState("GENERAL");
  const [formTitle, setFormTitle] = useState("");
  const [formBody, setFormBody] = useState("");
  const [formTargetDate, setFormTargetDate] = useState("");
  const [formTargetProvince, setFormTargetProvince] = useState("");
  const [formTargetRoles, setFormTargetRoles] = useState("");
  const [formVisibleUntil, setFormVisibleUntil] = useState("");

  const fetchAnnouncements = async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    try {
      const res = await fetch(`${getApiBaseUrl()}/announcements`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAnnouncements(Array.isArray(data) ? data : []);
      }
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAnnouncements(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const token = getTokenFromCookie();
    if (!token) return;

    const payload: Record<string, unknown> = {
      announcement_type: formType,
      title: formTitle,
      body: formBody,
    };
    if (formTargetDate) payload.target_date = new Date(formTargetDate).toISOString();
    if (formTargetProvince) payload.target_province = formTargetProvince;
    if (formTargetRoles) payload.target_roles = formTargetRoles;
    if (formVisibleUntil) payload.visible_until = new Date(formVisibleUntil).toISOString();

    try {
      const res = await fetch(`${getApiBaseUrl()}/announcements`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setShowForm(false);
        setFormTitle("");
        setFormBody("");
        setFormTargetDate("");
        setFormTargetProvince("");
        setFormTargetRoles("");
        setFormVisibleUntil("");
        fetchAnnouncements();
      }
    } catch { /* ignore */ } finally {
      setSaving(false);
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Duyuru Yonetimi</h1>
          <p className="text-sm text-slate-500">Ciftci ve pilotlarin sayfalarinda gorunecek duyurulari yonetin.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
          {showForm ? "Iptal" : "Yeni Duyuru"}
        </button>
      </div>

      {/* Yeni Duyuru Formu */}
      {showForm && (
        <form onSubmit={handleSubmit} className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Duyuru Turu *</label>
              <select value={formType} onChange={(e) => setFormType(e.target.value)} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm">
                {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Hedef Tarih (opsiyonel)</label>
              <input type="date" value={formTargetDate} onChange={(e) => setFormTargetDate(e.target.value)} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" />
              <p className="mt-0.5 text-xs text-slate-400">Ucus baslangic tarihi, kampanya bitis vb.</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">Baslik *</label>
            <input type="text" value={formTitle} onChange={(e) => setFormTitle(e.target.value)} required minLength={3} maxLength={200} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" placeholder="Orn: 2026 Yaz Sezonu Ucuslari Basliyor" />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">Icerik *</label>
            <textarea value={formBody} onChange={(e) => setFormBody(e.target.value)} required minLength={3} maxLength={2000} rows={3} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" placeholder="Duyuru detayi..." />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-slate-700">Hedef Il (opsiyonel)</label>
              <input type="text" value={formTargetProvince} onChange={(e) => setFormTargetProvince(e.target.value)} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" placeholder="Bos = tum iller" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Hedef Roller (opsiyonel)</label>
              <input type="text" value={formTargetRoles} onChange={(e) => setFormTargetRoles(e.target.value)} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" placeholder="FARMER_SINGLE,PILOT" />
              <p className="mt-0.5 text-xs text-slate-400">Bos = herkese gorunur</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Gecerlilik Bitis (opsiyonel)</label>
              <input type="date" value={formVisibleUntil} onChange={(e) => setFormVisibleUntil(e.target.value)} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>

          <button type="submit" disabled={saving} className="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50">
            {saving ? "Kaydediliyor..." : "Duyuruyu Yayinla"}
          </button>
        </form>
      )}

      {/* Mevcut Duyurular */}
      {loading ? (
        <p className="text-sm text-slate-500">Yukleniyor...</p>
      ) : announcements.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
          <p className="text-slate-500">Henuz duyuru yok.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {announcements.map((a) => (
            <div key={a.announcement_id} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${TYPE_BADGE[a.announcement_type] || "bg-slate-100 text-slate-700"}`}>
                    {TYPES.find((t) => t.value === a.announcement_type)?.label || a.announcement_type}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-900">{a.title}</h3>
                </div>
                <span className="text-xs text-slate-400">{new Date(a.created_at).toLocaleDateString("tr-TR")}</span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{a.body}</p>
              <div className="mt-2 flex gap-3 text-xs text-slate-400">
                {a.target_date && <span>Tarih: {new Date(a.target_date).toLocaleDateString("tr-TR")}</span>}
                {a.target_province && <span>Il: {a.target_province}</span>}
                {a.visible_until && <span>Bitis: {new Date(a.visible_until).toLocaleDateString("tr-TR")}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
