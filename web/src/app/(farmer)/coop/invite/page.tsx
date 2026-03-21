/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif / Uretici Birligi uye daveti — QR / 6 haneli davet kodu veya toplu CSV import. */
/* KR-063: Erisim: COOP_OWNER, COOP_ADMIN rolleri. */

'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { getApiBaseUrl, getTokenFromCookie } from '@/lib/api';
import { sanitizeText } from '@/lib/sanitize';

/** Davet turu: kooperatif veya uretici birligi */
type OrgType = 'COOP' | 'UNION';

interface InviteRecord {
  readonly code: string;
  readonly org_type: OrgType;
  readonly created_at: string;
  readonly status: 'ACTIVE' | 'USED' | 'EXPIRED';
}

interface CsvUploadResult {
  readonly imported: number;
  readonly errors: string[];
}

const ORG_LABELS: Record<OrgType, string> = {
  COOP: 'Kooperatif',
  UNION: 'Uretici Birligi',
};

export default function CoopInvitePage() {
  const router = useRouter();
  const [orgType, setOrgType] = useState<OrgType>('COOP');
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvResult, setCsvResult] = useState<CsvUploadResult | null>(null);
  const [invites, setInvites] = useState<readonly InviteRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(() => getTokenFromCookie(), []);

  // --- Mevcut davetleri listele ---
  const fetchInvites = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/coop/invites`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) { router.push('/login'); return; }
      if (!res.ok) return; // Endpoint henuz yoksa sessizce gec
      const data = (await res.json()) as { items?: InviteRecord[] };
      setInvites(data.items ?? []);
    } catch {
      // API endpoint henuz mevcut olmayabilir
    }
  }, [getToken, router]);

  useEffect(() => { fetchInvites(); }, [fetchInvites]);

  // --- Davet kodu olustur ---
  const handleGenerateCode = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setInviteCode(null);
    const token = getToken();
    if (!token) {
      setError('Oturum bulunamadi. Lutfen tekrar giris yapin.');
      return;
    }
    setLoading(true);
    try {
      const baseUrl = getApiBaseUrl();
      const res = await fetch(`${baseUrl}/coop/invites/generate`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ org_type: orgType }),
      });
      if (res.status === 401) { router.push('/login'); return; }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || 'Davet kodu olusturulamadi');
      }
      const data = (await res.json()) as { code: string };
      setInviteCode(data.code);
      await fetchInvites();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Bir hata olustu';
      setError(msg === 'Failed to fetch' ? 'Sunucuya baglanilamadi.' : msg);
    } finally {
      setLoading(false);
    }
  };

  // --- CSV toplu iceaktarim ---
  const handleCsvUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setError(null);
    setCsvResult(null);
    const token = getToken();
    if (!token) {
      setError('Oturum bulunamadi. Lutfen tekrar giris yapin.');
      return;
    }

    // Dosya boyutu kontrolu (maks 5MB)
    if (csvFile.size > 5 * 1024 * 1024) {
      setError('Dosya boyutu 5MB\'i asamaz.');
      return;
    }

    setLoading(true);
    try {
      const baseUrl = getApiBaseUrl();
      const formData = new FormData();
      formData.append('file', csvFile);
      formData.append('org_type', orgType);

      const res = await fetch(`${baseUrl}/coop/invites/bulk-import`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (res.status === 401) { router.push('/login'); return; }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || 'Toplu iceaktarim basarisiz');
      }
      const data = (await res.json()) as CsvUploadResult;
      setCsvResult(data);
      setCsvFile(null);
      await fetchInvites();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Bir hata olustu';
      setError(msg === 'Failed to fetch' ? 'Sunucuya baglanilamadi.' : msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      <h1 className="text-2xl font-semibold">Uye Davet Et</h1>

      {/* KR-014: Organizasyon turu secimi — Kooperatif veya Uretici Birligi */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Organizasyon Turu</h2>
        <div className="flex gap-4">
          {(Object.entries(ORG_LABELS) as [OrgType, string][]).map(([value, label]) => (
            <label key={value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="orgType"
                value={value}
                checked={orgType === value}
                onChange={() => setOrgType(value)}
                className="accent-emerald-600"
              />
              <span className="text-sm">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Hata mesaji */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      )}

      {/* KR-014: QR / 6 haneli davet kodu */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Davet Kodu ile Davet</h2>
        <p className="text-sm text-slate-600">
          6 haneli davet kodu olusturun. Ciftci bu kodu kendi hesabindan girerek{' '}
          {ORG_LABELS[orgType].toLowerCase()}nize katilabilir.
        </p>
        <form onSubmit={handleGenerateCode}>
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? 'Olusturuluyor...' : 'Davet Kodu Olustur'}
          </button>
        </form>
        {inviteCode && (
          <div className="mt-3 rounded bg-emerald-50 border border-emerald-200 p-4 text-center">
            <p className="text-xs text-emerald-700">Davet Kodu ({ORG_LABELS[orgType]}):</p>
            <p className="text-3xl font-mono font-bold tracking-widest text-emerald-800 my-2">{inviteCode}</p>
            <p className="text-xs text-slate-500">Bu kodu ciftciye iletin veya QR olarak paylasin.</p>
          </div>
        )}
      </div>

      {/* KR-014: Toplu CSV import */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
        <h2 className="font-medium">Toplu Iceaktarim (CSV)</h2>
        <p className="text-sm text-slate-600">
          Excel veya CSV dosyasiyla birden fazla uye ekleyin. Dosya: <strong>ad, soyad, telefon</strong> sutunlari icermelidir.
          Maksimum dosya boyutu: 5MB.
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
            disabled={!csvFile || loading}
            className="rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? 'Yukleniyor...' : 'Yukle'}
          </button>
        </form>

        {/* CSV sonuc mesaji */}
        {csvResult && (
          <div className="mt-3 space-y-2">
            <div className="rounded bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">
              {csvResult.imported} uye basariyla iceaktarildi.
            </div>
            {csvResult.errors.length > 0 && (
              <div className="rounded bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
                <p className="font-medium mb-1">Hatali satirlar:</p>
                <ul className="list-disc list-inside">
                  {csvResult.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* KR-014: Mevcut davet kodlari listesi */}
      {invites.length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
          <h2 className="font-medium">Mevcut Davet Kodlari</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-slate-600">
                <th className="pb-2">Kod</th>
                <th className="pb-2">Tur</th>
                <th className="pb-2">Olusturma</th>
                <th className="pb-2">Durum</th>
              </tr>
            </thead>
            <tbody>
              {invites.map((inv) => (
                <tr key={inv.code} className="border-b">
                  <td className="py-2 font-mono font-bold tracking-wider">{inv.code}</td>
                  <td className="py-2">{ORG_LABELS[inv.org_type] ?? inv.org_type}</td>
                  <td className="py-2 text-slate-500">{new Date(inv.created_at).toLocaleDateString('tr-TR')}</td>
                  <td className="py-2">
                    <span
                      className={
                        inv.status === 'ACTIVE'
                          ? 'text-emerald-600'
                          : inv.status === 'USED'
                            ? 'text-slate-400'
                            : 'text-amber-500'
                      }
                    >
                      {inv.status === 'ACTIVE' ? 'Aktif' : inv.status === 'USED' ? 'Kullanildi' : 'Suresi Doldu'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
