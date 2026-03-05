// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-013: Tarla kaydi: il, ilce, mahalle/koy, ada, parsel, alan (m2), bitki turu.
// KR-080: Tekil kayit kurali: il+ilce+mahalle/koy+ada+parsel kombinasyonu tekrar edemez.
'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

/** KR-013: Tarla ekleme payload'u — SSOT zorunlu alanlari. */
export interface AddFieldPayload {
  readonly province: string;
  readonly district: string;
  readonly village: string;
  readonly block: string;
  readonly parcel: string;
  readonly areaM2: number;
  readonly cropType: string;
  readonly requestId?: string;
  readonly corrId?: string;
}

interface AddFieldModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: AddFieldPayload) => Promise<void> | void;
  requestMeta?: { requestId?: string; corrId?: string };
}

export function AddFieldModal({ open, onClose, onSubmit, requestMeta }: AddFieldModalProps) {
  const [province, setProvince] = useState('');
  const [district, setDistrict] = useState('');
  const [village, setVillage] = useState('');
  const [block, setBlock] = useState('');
  const [parcel, setParcel] = useState('');
  const [areaM2, setAreaM2] = useState('');
  const [cropType, setCropType] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async () => {
    if (!province.trim()) return setError('İl zorunludur.');
    if (!district.trim()) return setError('İlçe zorunludur.');
    if (!village.trim()) return setError('Mahalle/Köy zorunludur.');
    if (!block.trim()) return setError('Ada zorunludur.');
    if (!parcel.trim()) return setError('Parsel zorunludur.');
    const area = Number(areaM2);
    if (!Number.isFinite(area) || area <= 0) return setError('Alan (m²) 0\'dan büyük olmalıdır.');
    if (!cropType.trim()) return setError('Bitki türü zorunludur.');

    setError(null);
    await onSubmit({
      province: province.trim(),
      district: district.trim(),
      village: village.trim(),
      block: block.trim(),
      parcel: parcel.trim(),
      areaM2: area,
      cropType: cropType.trim(),
      ...requestMeta,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" data-request-id={requestMeta?.requestId} data-corr-id={requestMeta?.corrId}>
      <div className="w-full max-w-lg rounded-lg bg-white p-5 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">Yeni Tarla Ekle</h2>
        <div className="mt-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="İl" value={province} onChange={(e) => setProvince(e.target.value)} hasError={!!error && !province.trim()} />
            <Input placeholder="İlçe" value={district} onChange={(e) => setDistrict(e.target.value)} hasError={!!error && !district.trim()} />
          </div>
          <Input placeholder="Mahalle / Köy" value={village} onChange={(e) => setVillage(e.target.value)} hasError={!!error && !village.trim()} />
          <div className="grid grid-cols-2 gap-3">
            <Input placeholder="Ada" value={block} onChange={(e) => setBlock(e.target.value)} hasError={!!error && !block.trim()} />
            <Input placeholder="Parsel" value={parcel} onChange={(e) => setParcel(e.target.value)} hasError={!!error && !parcel.trim()} />
          </div>
          <Input
            type="number"
            inputMode="decimal"
            min={0}
            step="1"
            placeholder="Alan (m²)"
            value={areaM2}
            onChange={(e) => setAreaM2(e.target.value)}
            hasError={!!error && Number(areaM2) <= 0}
          />
          <Input placeholder="Bitki Türü (örn. Pamuk)" value={cropType} onChange={(e) => setCropType(e.target.value)} hasError={!!error && !cropType.trim()} />
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>İptal</Button>
          <Button onClick={handleSubmit}>Kaydet</Button>
        </div>
      </div>
    </div>
  );
}
