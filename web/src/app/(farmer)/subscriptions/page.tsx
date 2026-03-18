/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-027: Sezonluk paket abonelik listesi — API'den cekilir, veri yoksa bilgi mesaji. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface Subscription {
  subscription_id: string;
  plan_code: string;
  start_date: string;
  status: string;
  field_id: string | null;
  crop_type: string | null;
  end_date: string | null;
  interval_days: number | null;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PENDING_PAYMENT: { label: "Odeme Bekleniyor", className: "bg-amber-100 text-amber-800" },
  ACTIVE: { label: "Aktif", className: "bg-emerald-100 text-emerald-800" },
  PAUSED: { label: "Duraklatildi", className: "bg-blue-100 text-blue-800" },
  CANCELLED: { label: "Iptal Edildi", className: "bg-slate-100 text-slate-600" },
  EXPIRED: { label: "Suresi Doldu", className: "bg-rose-100 text-rose-700" },
};

export default function FarmerSubscriptionsPage() {
  const router = useRouter();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscriptions = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) {
      setError("Oturum bulunamadi. Lutfen tekrar giris yapin.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/subscriptions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { router.push("/login"); return; }
      if (!res.ok) throw new Error("Abonelikler yuklenemedi");
      const data = (await res.json()) as Subscription[];
      setSubscriptions(data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata olustu");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => { fetchSubscriptions(); }, [fetchSubscriptions]);

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Abonelikler</h1>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>
      ) : subscriptions.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">HENUZ VERI-BILGI BULUNMAMAKTADIR</p>
          <p className="mt-2 text-sm text-slate-400">Abonelik olusturdugunuzda burada goruntulenecektir.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {subscriptions.map((s) => {
            const statusInfo = STATUS_LABELS[s.status] ?? { label: s.status, className: "bg-slate-100 text-slate-600" };
            return (
              <div key={s.subscription_id} className="rounded-lg border border-slate-200 bg-white p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-900">{s.plan_code.replace(/_/g, " ")}</p>
                  <p className="text-xs text-slate-500">Baslangic: {s.start_date}{s.end_date ? ` — Bitis: ${s.end_date}` : ""}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusInfo.className}`}>
                  {statusInfo.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
