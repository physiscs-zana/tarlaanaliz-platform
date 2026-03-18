/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme + manuel onay + audit akisi gorunur tutulur. */

'use client';

import { useCallback, useEffect, useState } from 'react';
import { getApiBaseUrl, getTokenFromCookie } from '@/lib/api';
import { IbanInstructions } from '@/components/features/payment/IbanInstructions';

type PaymentMethod = 'iban' | 'credit_card';

interface IbanInfo {
  iban: string;
  recipient: string;
}

export default function FarmerPaymentsPage() {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('iban');
  const [ibanInfo, setIbanInfo] = useState<IbanInfo>({ iban: '', recipient: '' });

  const fetchPaymentMethods = useCallback(async () => {
    try {
      const baseUrl = getApiBaseUrl();
      const token = getTokenFromCookie();
      const res = await fetch(`${baseUrl}/payments/methods`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = (await res.json()) as { methods: Array<{ code: string; iban?: string; recipient?: string }> };
        const ibanMethod = data.methods?.find((m) => m.code === 'IBAN');
        if (ibanMethod) {
          setIbanInfo({
            iban: ibanMethod.iban ?? '',
            recipient: ibanMethod.recipient ?? '',
          });
        }
      }
    } catch { /* fallback to empty */ }
  }, []);

  useEffect(() => { fetchPaymentMethods(); }, [fetchPaymentMethods]);

  return (
    <section className="space-y-6" aria-label="Farmer payments">
      <h1 className="text-2xl font-semibold">Odeme</h1>

      {/* Odeme yontemi secimi */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">Odeme Yontemi</h2>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setSelectedMethod('iban')}
            className={`flex-1 rounded-lg border-2 p-4 text-center transition-colors ${
              selectedMethod === 'iban'
                ? 'border-green-600 bg-green-50 text-green-800'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
            }`}
          >
            <span className="block text-lg font-semibold">Havale / EFT</span>
            <span className="block text-sm mt-1">IBAN ile odeme</span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedMethod('credit_card')}
            className={`flex-1 rounded-lg border-2 p-4 text-center transition-colors ${
              selectedMethod === 'credit_card'
                ? 'border-amber-500 bg-amber-50 text-amber-800'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
            }`}
          >
            <span className="block text-lg font-semibold">Kredi Karti</span>
            <span className="block text-sm mt-1">Online odeme</span>
          </button>
        </div>
      </div>

      {/* IBAN ile odeme */}
      {selectedMethod === 'iban' && ibanInfo.iban && (
        <IbanInstructions
          iban={ibanInfo.iban}
          recipientName={ibanInfo.recipient}
          amount=""
          fieldId=""
        />
      )}

      {/* Kredi karti uyarisi */}
      {selectedMethod === 'credit_card' && (
        <div className="rounded-lg border-2 border-amber-400 bg-amber-50 p-6 text-center space-y-3">
          <div className="text-4xl">&#9888;</div>
          <h3 className="text-xl font-bold text-amber-800">
            SU ANDA SADECE IBAN ILE ODEME ALABILIYORUZ
          </h3>
          <p className="text-amber-700">
            Kredi karti ile odeme secenegi yakin zamanda aktif olacaktir.
            Lutfen havale/EFT yontemiyle odeme yapiniz.
          </p>
          <button
            type="button"
            onClick={() => setSelectedMethod('iban')}
            className="mt-2 rounded-lg bg-green-600 px-6 py-2 text-white font-medium hover:bg-green-700 transition-colors"
          >
            IBAN ile Odeme Yap
          </button>
        </div>
      )}
    </section>
  );
}
