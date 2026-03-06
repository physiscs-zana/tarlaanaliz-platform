// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
import { PaymentStatusBadge, type PaymentStatus } from './PaymentStatusBadge';

interface DekontViewerProps {
  receiptUrl?: string;
  status: PaymentStatus;
  paymentIntentId?: string;
  requestMeta?: { requestId?: string; corrId?: string };
}

export function DekontViewer({ receiptUrl, status, paymentIntentId, requestMeta }: DekontViewerProps) {
  const showApprovalWarning = status === 'PAID' && !paymentIntentId;

  return (
    <section className="rounded-lg border border-slate-200 p-4" data-request-id={requestMeta?.requestId} data-corr-id={requestMeta?.corrId}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-900">Dekont Görüntüleyici</h3>
        <PaymentStatusBadge status={status} />
      </div>
      {/* KR-033 */}
      {showApprovalWarning ? (
        <p className="mb-2 text-sm text-rose-700">PaymentIntent olmadan approved/paid durumu gösterilemez.</p>
      ) : null}
      {receiptUrl ? (
        <a href={receiptUrl} target="_blank" rel="noreferrer" className="text-sm text-emerald-700 underline">
          Dekontu aç
        </a>
      ) : (
        <p className="text-sm text-slate-500">Henüz dekont yüklenmedi.</p>
      )}
    </section>
  );
}
