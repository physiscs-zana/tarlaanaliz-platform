/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: payment + manuel onay + audit akisi zorunlu gorunurluk. */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  payer_phone: string | null;
  payer_province: string | null;
  payer_district: string | null;
  payment_ref: string | null;
  sla_deadline: string | null;
  sla_overdue: boolean;
}

interface ReceiptModalState {
  open: boolean;
  loading: boolean;
  error: string | null;
  blobUrl: string | null;
  blobId: string | null;
  isPdf: boolean;
  payerName: string | null;
  paymentRef: string | null;
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

function maskPhone(phone: string | null): string {
  if (!phone) return "\u2014";
  if (phone.length >= 10) {
    return phone.slice(0, 4) + "***" + phone.slice(-2);
  }
  return phone;
}

/* ─── Receipt Modal ─── */

function ReceiptModal({
  state,
  onClose,
}: {
  readonly state: ReceiptModalState;
  readonly onClose: () => void;
}) {
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    if (!state.open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state.open, onClose]);

  // Reset zoom on new receipt
  useEffect(() => { setZoom(1); }, [state.blobUrl]);

  if (!state.open) return null;

  const handleDownload = () => {
    if (!state.blobUrl || !state.blobId) return;
    const a = document.createElement("a");
    a.href = state.blobUrl;
    a.download = state.blobId;
    a.click();
  };

  const zoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const zoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const zoomReset = () => setZoom(1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative mx-4 flex max-h-[90vh] w-full max-w-4xl flex-col rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Dekont Goruntuleme</h3>
            <p className="text-xs text-slate-500">
              {state.payerName ?? ""} {state.paymentRef ? `— ${state.paymentRef}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Zoom controls */}
            {!state.isPdf && state.blobUrl && (
              <div className="flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1">
                <button type="button" onClick={zoomOut} className="text-sm text-slate-600 hover:text-slate-900 px-1" title="Kucult">−</button>
                <button type="button" onClick={zoomReset} className="text-xs text-slate-500 hover:text-slate-900 px-1 min-w-[3rem] text-center" title="Sifirla">
                  {Math.round(zoom * 100)}%
                </button>
                <button type="button" onClick={zoomIn} className="text-sm text-slate-600 hover:text-slate-900 px-1" title="Buyut">+</button>
              </div>
            )}
            {/* Download */}
            {state.blobUrl && (
              <button
                type="button"
                onClick={handleDownload}
                className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
              >
                Indir
              </button>
            )}
            {/* Close */}
            <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-500 hover:bg-slate-50 transition" title="Kapat">
              ✕
            </button>
          </div>
        </div>

        {/* Body */}
        <div ref={containerRef} className="flex-1 overflow-auto bg-slate-100 p-4">
          {state.loading && (
            <div className="flex h-64 items-center justify-center text-sm text-slate-500">Dekont yukleniyor...</div>
          )}
          {state.error && (
            <div className="flex h-64 items-center justify-center text-sm text-rose-600">{state.error}</div>
          )}
          {state.blobUrl && !state.loading && !state.error && (
            state.isPdf ? (
              <iframe
                src={state.blobUrl}
                title="Dekont PDF"
                className="h-[70vh] w-full rounded border border-slate-200 bg-white"
              />
            ) : (
              <div className="flex justify-center overflow-auto">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={state.blobUrl}
                  alt="Dekont"
                  className="rounded border border-slate-200 shadow-sm transition-transform duration-150"
                  style={{ transform: `scale(${zoom})`, transformOrigin: "top center" }}
                />
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Payment Table ─── */

function PaymentTable({
  payments,
  title,
  emptyMsg,
  onViewReceipt,
}: {
  payments: PaymentItem[];
  title: string;
  emptyMsg: string;
  onViewReceipt: (p: PaymentItem) => void;
}) {
  if (payments.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 py-8 text-center">
        <p className="text-sm text-slate-400">{emptyMsg}</p>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="border-b border-slate-100 bg-slate-50">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Referans</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Ciftci</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Telefon</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Il / Ilce</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Tutar</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Dekont</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Durum</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">SLA</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-slate-600">Tarih</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {payments.map((p) => {
            const si = STATUS_LABELS[p.status] ?? { label: p.status, className: "bg-slate-100 text-slate-600" };
            const location = [p.payer_province, p.payer_district].filter(Boolean).join(" / ");
            return (
              <tr key={p.intent_id} className="hover:bg-slate-50">
                <td className="px-3 py-2 font-mono text-xs">{p.payment_ref ?? p.intent_id.slice(0, 8)}</td>
                <td className="px-3 py-2 text-xs text-slate-700">{p.payer_display_name ?? "\u2014"}</td>
                <td className="px-3 py-2 text-xs text-slate-600">{maskPhone(p.payer_phone)}</td>
                <td className="px-3 py-2 text-xs text-slate-600">{location || "\u2014"}</td>
                <td className="px-3 py-2 text-xs font-medium">{formatAmount(p.amount)}</td>
                <td className="px-3 py-2">
                  {p.receipt_blob_id ? (
                    <button
                      type="button"
                      onClick={() => onViewReceipt(p)}
                      className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 underline hover:bg-emerald-100 transition cursor-pointer"
                    >
                      Goruntule
                    </button>
                  ) : (
                    <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">Bekleniyor</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${si.className}`}>{si.label}</span>
                </td>
                <td className="px-3 py-2 text-xs">
                  {p.sla_overdue ? (
                    <span className="inline-block rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700">SLA Asim!</span>
                  ) : p.sla_deadline ? (
                    <span className="text-slate-400">{new Date(p.sla_deadline).toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>
                  ) : (
                    <span className="text-slate-300">{"\u2014"}</span>
                  )}
                </td>
                <td className="px-3 py-2 text-xs text-slate-500">{new Date(p.created_at).toLocaleDateString("tr-TR")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Page ─── */

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modal, setModal] = useState<ReceiptModalState>({
    open: false,
    loading: false,
    error: null,
    blobUrl: null,
    blobId: null,
    isPdf: false,
    payerName: null,
    paymentRef: null,
  });

  const closeModal = useCallback(() => {
    setModal((prev) => {
      if (prev.blobUrl) URL.revokeObjectURL(prev.blobUrl);
      return { open: false, loading: false, error: null, blobUrl: null, blobId: null, isPdf: false, payerName: null, paymentRef: null };
    });
  }, []);

  const openReceipt = useCallback(async (p: PaymentItem) => {
    if (!p.receipt_blob_id) return;
    const token = getTokenFromCookie();
    if (!token) return;

    const isPdf = p.receipt_blob_id.toLowerCase().endsWith(".pdf");

    setModal({
      open: true,
      loading: true,
      error: null,
      blobUrl: null,
      blobId: p.receipt_blob_id,
      isPdf,
      payerName: p.payer_display_name,
      paymentRef: p.payment_ref,
    });

    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/admin/payments/receipts/${encodeURIComponent(p.receipt_blob_id)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        setModal((prev) => ({ ...prev, loading: false, error: "Dekont dosyasi yuklenemedi." }));
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setModal((prev) => ({ ...prev, loading: false, blobUrl: url }));
    } catch {
      setModal((prev) => ({ ...prev, loading: false, error: "Baglanti hatasi." }));
    }
  }, []);

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

  const eftPayments = payments.filter((p) => p.package_code === "IBAN_TRANSFER" || !p.package_code?.includes("CREDIT"));
  const cardPayments = payments.filter((p) => p.package_code === "CREDIT_CARD");

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Odeme Inceleme</h1>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      <div className="space-y-6">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">Havale / EFT</h2>
          <PaymentTable payments={eftPayments} title="EFT" emptyMsg="Bekleyen EFT odemesi yok." onViewReceipt={openReceipt} />
        </div>
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700">Kredi Karti</h2>
          <PaymentTable payments={cardPayments} title="Kredi Karti" emptyMsg="Kredi karti odemesi henuz aktif degil." onViewReceipt={openReceipt} />
        </div>
      </div>

      {payments.length === 0 && !error && (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
          <p className="text-lg font-medium text-slate-500">Bekleyen odeme bulunmamaktadir.</p>
          <p className="mt-1 text-sm text-slate-400">Ciftciler odeme olusturduklarinda burada gorunecektir.</p>
        </div>
      )}

      {/* Receipt Viewer Modal */}
      <ReceiptModal state={modal} onClose={closeModal} />
    </section>
  );
}
