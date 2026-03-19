/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: payment + manuel onay + audit akisi zorunlu gorunurluk. */

"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

interface PaymentItem {
  intent_id: string;
  status: string;
  amount: number;
  season: string;
  package_code: string;
  field_ids: string[];
  created_at: string;
  receipt_blob_id: string | null;
  payer_display_name: string | null;
  payment_ref: string | null;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PENDING_RECEIPT: { label: "Dekont Bekleniyor", className: "bg-amber-50 text-amber-700" },
  PENDING_ADMIN_REVIEW: { label: "Admin Onay Bekliyor", className: "bg-blue-50 text-blue-700" },
  PAID: { label: "Odendi", className: "bg-emerald-50 text-emerald-700" },
  REJECTED: { label: "Reddedildi", className: "bg-rose-50 text-rose-700" },
  PAYMENT_PENDING: { label: "Odeme Bekleniyor", className: "bg-amber-50 text-amber-700" },
  CANCELLED: { label: "Iptal", className: "bg-slate-100 text-slate-500" },
  REFUNDED: { label: "Iade Edildi", className: "bg-sky-50 text-sky-700" },
};

function formatAmount(kurus: number): string {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(kurus / 100);
}

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPayments = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) { setLoading(false); return; }
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/payments/intents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as PaymentItem[];
        setPayments(data ?? []);
      }
    } catch { setError("Odeme listesi yuklenemedi."); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchPayments(); }, [fetchPayments]);

  if (loading) return <div className="py-12 text-center text-sm text-slate-500">Yukleniyor...</div>;

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Odeme Inceleme</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
      {payments.length === 0 && !error ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <p className="text-lg font-medium text-slate-500">Bekleyen odeme bulunmamaktadir.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Referans</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Ciftci</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Tutar</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Paket</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Dekont</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Durum</th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">Tarih</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {payments.map((p) => {
                const statusInfo = STATUS_LABELS[p.status] ?? { label: p.status, className: "bg-slate-100 text-slate-600" };
                return (
                  <tr key={p.intent_id} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-mono text-xs">{p.payment_ref ?? p.intent_id.slice(0, 8)}</td>
                    <td className="px-4 py-2.5 text-slate-700">{p.payer_display_name ?? "—"}</td>
                    <td className="px-4 py-2.5 font-medium">{formatAmount(p.amount)}</td>
                    <td className="px-4 py-2.5 text-slate-600">{p.package_code}</td>
                    <td className="px-4 py-2.5">
                      {p.receipt_blob_id ? (
                        <span className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">Yuklendi</span>
                      ) : (
                        <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">Bekleniyor</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusInfo.className}`}>
                        {statusInfo.label}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">{new Date(p.created_at).toLocaleDateString("tr-TR")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
