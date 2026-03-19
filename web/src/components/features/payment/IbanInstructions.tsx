// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033 §3c: IBAN Talimat Ekrani (PWA)
// IBAN (kopyala), alici adi, tutar, "Tarla Kodunuzu yaziniz" (kopyala), dekont yukleme, bilgi notu.
'use client';

import { useState } from 'react';

interface IbanInstructionsProps {
  readonly iban: string;
  readonly recipientName: string;
  readonly amount: string;
  readonly fieldCode: string;
  readonly corrId?: string;
  readonly requestId?: string;
}

function CopyButton({ text, label }: { readonly text: string; readonly label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may not be available
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-2 rounded border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50"
      aria-label={`${label} kopyala`}
    >
      {copied ? 'Kopyalandı' : 'Kopyala'}
    </button>
  );
}

export function IbanInstructions({ iban, recipientName, amount, fieldCode, corrId, requestId }: IbanInstructionsProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 space-y-4" data-corr-id={corrId} data-request-id={requestId}>
      <h2 className="text-lg font-semibold">Havale / EFT Bilgileri</h2>

      <div className="space-y-2 text-sm">
        <div className="flex items-center">
          <span className="font-medium w-28">IBAN:</span>
          <code className="bg-slate-50 px-2 py-1 rounded text-sm">{iban}</code>
          <CopyButton text={iban} label="IBAN" />
        </div>

        <div className="flex items-center">
          <span className="font-medium w-28">Alıcı Adı:</span>
          <span>{recipientName}</span>
        </div>

        <div className="flex items-center">
          <span className="font-medium w-28">Tutar:</span>
          <span className="font-semibold">{amount}</span>
        </div>

        <div className="flex items-center">
          <span className="font-medium w-28">Tarla Kodu:</span>
          <code className="bg-slate-50 px-2 py-1 rounded text-sm">{fieldCode}</code>
          <CopyButton text={fieldCode} label="Tarla Kodu" />
        </div>
      </div>

      <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
        <p className="font-medium">Havale aciklamasina Tarla Kodunuzu yaziniz.</p>
        <p className="mt-1">Dekontu asagidan yukleyiniz.</p>
      </div>

      <p className="text-xs text-slate-500">
        Ödemeniz Merkez Yönetim tarafından onaylandığında hesabınızda bildirim alacaksınız.
      </p>
    </div>
  );
}
