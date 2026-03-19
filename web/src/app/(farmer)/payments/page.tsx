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
  field_name: string;
  area_ha: number;
  crop_type: string | null;
}

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

export default function FarmerPaymentsPage() {
  const [ibanInfo, setIbanInfo] = useState<IbanInfo>({ iban: '', recipient: '', bank_name: '' });
  const [fields, setFields] = useState<FieldItem[]>([]);
  const [selectedFieldId, setSelectedFieldId] = useState('');

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
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const selectedField = fields.find((f) => f.field_id === selectedFieldId);

  return (
    <section className="space-y-6" aria-label="Farmer payments">
      <h1 className="text-2xl font-semibold">Odeme</h1>

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
              <span>Tarla ID:</span>
              <code className="bg-slate-50 px-2 py-1 rounded">{selectedField.field_id}</code>
              <CopyButton text={selectedField.field_id} />
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
            <p className="font-medium">Havale aciklamasina Tarla ID numaranizi yaziniz.</p>
            {selectedField && (
              <p>Tarla ID: <code className="bg-amber-100 px-1 rounded">{selectedField.field_id.slice(0, 8)}...</code></p>
            )}
          </div>

          <p className="text-xs text-slate-500">
            Odemeniz Merkez Yonetim tarafindan onaylandiginda hesabinizda bildirim alacaksiniz.
          </p>
        </div>
      ) : (
        <div className="py-8 text-center text-sm text-slate-500">Odeme bilgileri yukleniyor...</div>
      )}

      {/* Kredi karti uyarisi */}
      <div className="rounded-lg border border-slate-200 bg-white p-5 text-center space-y-2">
        <p className="text-sm font-medium text-slate-600">Kredi Karti ile Odeme</p>
        <p className="text-xs text-slate-400">Kredi karti ile odeme secenegi yakin zamanda aktif olacaktir.</p>
      </div>
    </section>
  );
}
