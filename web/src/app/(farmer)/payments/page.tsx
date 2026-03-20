/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme + manuel onay + audit akisi gorunur tutulur. */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { getApiBaseUrl, getTokenFromCookie } from '@/lib/api';

interface IbanInfo {
  iban: string;
  recipient: string;
  bank_name: string;
}

interface FieldItem {
  field_id: string;
  field_code: string;
  field_name: string;
  area_ha: number;
  crop_type: string | null;
}

interface MyReceipt {
  intent_id: string;
  payment_ref: string | null;
  amount_tl: number;
  method: string;
  status: string;
  status_message: string;
  receipt_uploaded: boolean;
  created_at: string;
}

const RECEIPT_STATUS_LABELS: Record<string, { label: string; className: string }> = {
  PAYMENT_PENDING: { label: "Odeme Bekleniyor", className: "bg-amber-50 text-amber-700" },
  PENDING_ADMIN_REVIEW: { label: "Inceleniyor", className: "bg-blue-50 text-blue-700" },
  PAID: { label: "Onaylandi", className: "bg-emerald-50 text-emerald-700" },
  REJECTED: { label: "Reddedildi", className: "bg-rose-50 text-rose-700" },
  CANCELLED: { label: "Iptal", className: "bg-slate-100 text-slate-500" },
  REFUNDED: { label: "Iade Edildi", className: "bg-sky-50 text-sky-700" },
};

function CopyButton({ text }: { readonly text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* noop */ }
  };
  return (
    <button type="button" onClick={handleCopy} className="ml-2 rounded border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50">
      {copied ? 'Kopyalandi' : 'Kopyala'}
    </button>
  );
}

function ReceiptUpload({ fieldId, onUploadSuccess }: { readonly fieldId: string; readonly onUploadSuccess?: () => void }) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    if (file.type.startsWith('image/')) {
      setPreview(URL.createObjectURL(file));
    }

    const token = getTokenFromCookie();
    if (!token) { setResult({ type: 'err', text: 'Oturum bulunamadi.' }); return; }

    setUploading(true);
    setResult(null);
    try {
      const baseUrl = getApiBaseUrl();
      const formData = new FormData();
      formData.append('file', file);
      formData.append('field_id', fieldId);

      const res = await fetch(`${baseUrl}/payments/upload-receipt`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        setResult({ type: 'ok', text: 'Dekont yuklendi. Merkez Yonetim tarafindan onaylanacaktir.' });
        onUploadSuccess?.();
      } else {
        const body = await res.json().catch(() => ({}));
        setResult({ type: 'err', text: (body as { detail?: string }).detail || 'Yuklenemedi.' });
      }
    } catch {
      setResult({ type: 'err', text: 'Baglanti hatasi.' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
      <h2 className="text-lg font-semibold">Dekont Yukle</h2>
      <p className="text-xs text-slate-500">Havale/EFT yaptiktan sonra dekont fotografini veya PDF dosyasini yukleyin.</p>

      <label className="flex cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 hover:border-emerald-400 hover:bg-emerald-50/30 transition">
        <input type="file" accept="image/*,.pdf" onChange={handleUpload} className="hidden" disabled={uploading} />
        <div className="text-center">
          {uploading ? (
            <p className="text-sm text-slate-500">Yukleniyor...</p>
          ) : (
            <>
              <div className="text-3xl text-slate-300">&#128206;</div>
              <p className="mt-1 text-sm font-medium text-slate-600">Dekont secmek icin tiklayin</p>
              <p className="text-xs text-slate-400">JPEG, PNG, WebP veya PDF (maks. 10 MB)</p>
            </>
          )}
        </div>
      </label>

      {preview && (
        <div className="flex justify-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={preview} alt="Dekont onizleme" className="max-h-48 rounded border border-slate-200" />
        </div>
      )}

      {result && (
        <div className={`rounded-lg border p-3 text-sm ${result.type === 'ok' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-rose-200 bg-rose-50 text-rose-700'}`}>
          {result.text}
        </div>
      )}
    </div>
  );
}

function MyReceiptsPanel({ receipts, loading }: { readonly receipts: MyReceipt[]; readonly loading: boolean }) {
  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold mb-3">Dekontlarim</h2>
        <div className="py-8 text-center text-sm text-slate-500">Yukleniyor...</div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
      <h2 className="text-lg font-semibold">Dekontlarim</h2>

      {receipts.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 py-8 text-center">
          <p className="text-sm text-slate-400">Henuz dekont bulunmamaktadir.</p>
          <p className="mt-1 text-xs text-slate-300">Odeme yapip dekont yukledikten sonra burada gorunecektir.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {receipts.map((r) => {
            const si = RECEIPT_STATUS_LABELS[r.status] ?? { label: r.status, className: "bg-slate-100 text-slate-600" };
            return (
              <div key={r.intent_id} className="rounded-lg border border-slate-100 bg-slate-50 p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-600">{r.payment_ref ?? r.intent_id.slice(0, 8)}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${si.className}`}>{si.label}</span>
                </div>
                {r.amount_tl > 0 && (
                  <p className="text-sm font-medium text-slate-800">
                    {new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(r.amount_tl)}
                  </p>
                )}
                <p className="text-xs text-slate-500">{r.status_message}</p>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>{new Date(r.created_at).toLocaleDateString("tr-TR")}</span>
                  <span>{r.receipt_uploaded ? "Dekont yuklendi" : "Dekont bekleniyor"}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function FarmerPaymentsPage() {
  const [ibanInfo, setIbanInfo] = useState<IbanInfo>({ iban: '', recipient: '', bank_name: '' });
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState('');
  const [receipts, setReceipts] = useState<MyReceipt[]>([]);
  const [receiptsLoading, setReceiptsLoading] = useState(true);

  const fetchData = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    const baseUrl = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };

    // Fetch IBAN info
    try {
      const res = await fetch(`${baseUrl}/payments/methods`, { headers });
      if (res.ok) {
        const data = (await res.json()) as { methods: Array<{ code: string; iban?: string; recipient?: string; bank_name?: string }> };
        const m = data.methods?.find((x) => x.code === 'IBAN');
        if (m) setIbanInfo({ iban: m.iban ?? '', recipient: m.recipient ?? '', bank_name: m.bank_name ?? '' });
      }
    } catch { /* noop */ }

    // Fetch fields
    try {
      const res = await fetch(`${baseUrl}/fields`, { headers });
      if (res.ok) {
        const data = (await res.json()) as { items: FieldItem[] };
        setFields(data.items ?? []);
        if (data.items?.length) setSelectedFieldId(data.items[0].field_id);
      }
    } catch { /* noop */ }

    // Fetch my receipts/payment status
    setReceiptsLoading(true);
    try {
      const res = await fetch(`${baseUrl}/payments/my-status`, { headers });
      if (res.ok) {
        const data = (await res.json()) as { payments: MyReceipt[] };
        setReceipts(data.payments ?? []);
      }
    } catch { /* noop */ }
    setReceiptsLoading(false);
  }, []);

  const refreshReceipts = useCallback(async () => {
    const token = getTokenFromCookie();
    if (!token) return;
    const baseUrl = getApiBaseUrl();
    try {
      const res = await fetch(`${baseUrl}/payments/my-status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = (await res.json()) as { payments: MyReceipt[] };
        setReceipts(data.payments ?? []);
      }
    } catch { /* noop */ }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const selectedField = fields.find((f) => f.field_id === selectedFieldId);

  return (
    <section className="space-y-6" aria-label="Farmer payments">
      <h1 className="text-2xl font-semibold">Odeme</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sol Kolon: Odeme Bilgileri & Dekont Yukleme */}
        <div className="space-y-6">
          {/* Tarla secimi */}
          {fields.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
              <h2 className="text-sm font-semibold text-slate-600">Hangi tarla icin odeme yapacaksiniz?</h2>
              <select
                value={selectedFieldId}
                onChange={(e) => setSelectedFieldId(e.target.value)}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              >
                {fields.map((f) => (
                  <option key={f.field_id} value={f.field_id}>
                    {f.field_name} — {(f.area_ha * 10).toFixed(1)} donum
                  </option>
                ))}
              </select>
              {selectedField && (
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>Tarla Kodu:</span>
                  <code className="bg-slate-50 px-2 py-1 rounded">{selectedField.field_code}</code>
                  <CopyButton text={selectedField.field_code} />
                </div>
              )}
            </div>
          )}

          {/* IBAN Bilgileri */}
          {ibanInfo.iban ? (
            <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
              <h2 className="text-lg font-semibold">Havale / EFT Bilgileri</h2>
              <div className="space-y-2 text-sm">
                <div className="flex items-center">
                  <span className="font-medium w-28">IBAN:</span>
                  <code className="bg-slate-50 px-2 py-1 rounded">{ibanInfo.iban}</code>
                  <CopyButton text={ibanInfo.iban.replace(/\s/g, '')} />
                </div>
                <div className="flex items-center">
                  <span className="font-medium w-28">Banka:</span>
                  <span>{ibanInfo.bank_name}</span>
                </div>
                <div className="flex items-center">
                  <span className="font-medium w-28">Alici Adi:</span>
                  <span>{ibanInfo.recipient}</span>
                </div>
              </div>

              <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 space-y-1">
                <p className="font-medium">Havale aciklamasina Tarla Kodunuzu yaziniz.</p>
                {selectedField && (
                  <p>Tarla Kodu: <code className="bg-amber-100 px-1 rounded">{selectedField.field_code}</code></p>
                )}
              </div>

              <p className="text-xs text-slate-500">
                Odemeniz Merkez Yonetim tarafindan onaylandiginda hesabinizda bildirim alacaksiniz.
              </p>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-slate-500">Odeme bilgileri yukleniyor...</div>
          )}

          {/* Dekont Yukleme */}
          {selectedFieldId && (
            <ReceiptUpload fieldId={selectedFieldId} onUploadSuccess={refreshReceipts} />
          )}

          {/* Kredi karti uyarisi */}
          <div className="rounded-lg border border-slate-200 bg-white p-5 text-center space-y-2">
            <p className="text-sm font-medium text-slate-600">Kredi Karti ile Odeme</p>
            <p className="text-xs text-slate-400">Kredi karti ile odeme secenegi yakin zamanda aktif olacaktir.</p>
          </div>
        </div>

        {/* Sag Kolon: Dekontlarim */}
        <div>
          <MyReceiptsPanel receipts={receipts} loading={receiptsLoading} />
        </div>
      </div>
    </section>
  );
}
