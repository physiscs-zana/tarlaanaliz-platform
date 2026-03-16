/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: odeme + manuel onay + audit akisi gorunur tutulur. */

'use client';

import { useState } from 'react';
import { IbanInstructions } from '@/components/features/payment/IbanInstructions';

const COMPANY_IBAN = 'TR33 0006 1005 1978 6457 8413 26';
const COMPANY_NAME = 'TarlaAnaliz Tarim Teknolojileri A.S.';

type PaymentMethod = 'iban' | 'credit_card';

export default function FarmerPaymentsPage() {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod>('iban');

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
      {selectedMethod === 'iban' && (
        <IbanInstructions
          iban={COMPANY_IBAN}
          recipientName={COMPANY_NAME}
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
