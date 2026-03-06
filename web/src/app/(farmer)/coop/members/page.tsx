/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-014: Kooperatif uye yonetimi — davet, onaylama, listeleme. */
/* KR-063: Erisim: COOP_OWNER, COOP_ADMIN rolleri. */

'use client';

import { useState } from 'react';

interface CoopMember {
  readonly id: string;
  readonly name: string;
  readonly phone: string;
  readonly status: 'ACTIVE' | 'PENDING' | 'INACTIVE';
  readonly role: 'COOP_OWNER' | 'COOP_ADMIN' | 'COOP_AGRONOMIST' | 'COOP_VIEWER';
}

const STATUS_LABEL: Record<CoopMember['status'], string> = {
  ACTIVE: 'Aktif',
  PENDING: 'Onay Bekliyor',
  INACTIVE: 'Pasif',
};

const ROLE_LABEL: Record<CoopMember['role'], string> = {
  COOP_OWNER: 'Kooperatif Sahibi',
  COOP_ADMIN: 'Kooperatif Admin',
  COOP_AGRONOMIST: 'Agronomist',
  COOP_VIEWER: 'Izleyici',
};

export default function CoopMembersPage() {
  const [members] = useState<readonly CoopMember[]>([]);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Kooperatif Uyeleri</h1>
        <a href="/coop/invite" className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800">
          Uye Davet Et
        </a>
      </div>

      {members.length === 0 ? (
        <p className="text-sm text-slate-500">Henuz uye bulunmuyor. Uye davet etmek icin butonu kullanin.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-slate-600">
              <th className="pb-2">Ad</th>
              <th className="pb-2">Telefon</th>
              <th className="pb-2">Rol</th>
              <th className="pb-2">Durum</th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} className="border-b">
                <td className="py-2">{m.name}</td>
                <td className="py-2">{m.phone}</td>
                <td className="py-2">{ROLE_LABEL[m.role]}</td>
                <td className="py-2">{STATUS_LABEL[m.status]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
