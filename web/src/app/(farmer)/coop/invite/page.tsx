/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif uye daveti — QR / 6 haneli davet kodu veya toplu CSV import. */

'use client';

import { FormEvent, useState } from 'react';

export default function CoopInvitePage() {
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);

  const handleGenerateCode = async (e: FormEvent) => {
    e.preventDefault();
    // KR-014: 6 haneli davet kodu uretimi — API'den gelecek
    const code = Math.random().toString(10).slice(2, 8).padStart(6, '0');
    setInviteCode(code);
  };

  const handleCsvUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    // KR-014: Toplu iceaktarim (Excel/CSV) — API'ye gonderilecek
    // TODO: API entegrasyonu
  };

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Uye Davet Et</h1>

      {/* KR-014: QR / 6 haneli davet kodu */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Davet Kodu ile Davet</h2>
        <p className="text-sm text-slate-600">
          6 haneli davet kodu olusturun. Ciftci bu kodu kendi hesabindan girerek kooperatifinize katilabilir.
        </p>
        <form onSubmit={handleGenerateCode}>
          <button type="submit" className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">
            Davet Kodu Olustur
          </button>
        </form>
        {inviteCode && (
          <div className="mt-3 rounded bg-slate-100 p-3 text-center">
            <p className="text-xs text-slate-600">Davet Kodu:</p>
            <p className="text-2xl font-mono font-bold tracking-widest">{inviteCode}</p>
            <p className="mt-1 text-xs text-slate-500">Bu kodu ciftciye iletin veya QR olarak paylasin.</p>
          </div>
        )}
      </div>

      {/* KR-014: Toplu CSV import */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Toplu Iceaktarim (CSV)</h2>
        <p className="text-sm text-slate-600">
          Excel veya CSV dosyasiyla birden fazla uye ekleyin. Dosya: ad, soyad, telefon numarasi sutunlari icermelidir.
        </p>
        <form onSubmit={handleCsvUpload} className="flex items-center gap-3">
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
          <button
            type="submit"
            disabled={!csvFile}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50"
          >
            Yukle
          </button>
        </form>
      </div>
    </section>
  );
}
