/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-033: ödeme + manuel onay + audit akışı görünür tutulur. */

'use client';

import { PaymentStatusBadge } from '@/components/features/payment/PaymentStatusBadge';
import type { PaymentStatus } from '@/components/features/payment/PaymentStatusBadge';

/** Stub: gerçek veri API'den gelecek. */
const STUB_PAYMENTS: readonly { id: string; fieldId: string; amount: number; status: PaymentStatus; createdAt: string }[] = [
  { id: 'pay_001', fieldId: 'fld_1001', amount: 825, status: 'PAYMENT_PENDING', createdAt: '2026-03-01' },
  { id: 'pay_002', fieldId: 'fld_1002', amount: 1200, status: 'PAID', createdAt: '2026-02-20' },
];

export default function FarmerPaymentsPage() {
  return (
    <section className="space-y-4" aria-label="Farmer payments" data-corr-id="pending" data-request-id="pending">
      <h1 className="text-2xl font-semibold">Ödemeler</h1>

      {STUB_PAYMENTS.map((p) => (
        <article key={p.id} className="rounded-lg border border-slate-200 bg-white p-4 text-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">Tarla: {p.fieldId}</span>
            <span className="text-slate-500">{p.createdAt}</span>
          </div>
          <p>Tutar: {p.amount.toLocaleString('tr-TR')} TL</p>
          <PaymentStatusBadge status={p.status} showDescription />
        </article>
      ))}

      {STUB_PAYMENTS.length === 0 && (
        <p className="text-sm text-slate-500">Henüz ödeme kaydınız bulunmuyor.</p>
      )}
    </section>
  );
}
