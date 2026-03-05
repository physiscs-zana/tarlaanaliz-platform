// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: PaymentIntent.status kanonik degerleri: PAYMENT_PENDING | PAID | REJECTED | CANCELLED | REFUNDED
import { Badge } from '@/components/ui/badge';

/** KR-033: Kanonik odeme durumu enum'u (SSOT ile birebir). */
export type PaymentStatus = 'PAYMENT_PENDING' | 'PAID' | 'REJECTED' | 'CANCELLED' | 'REFUNDED';

const BADGE_VARIANT: Record<PaymentStatus, string> = {
  PAYMENT_PENDING: 'warning',
  PAID: 'success',
  REJECTED: 'danger',
  CANCELLED: 'secondary',
  REFUNDED: 'info',
} as const;

const STATUS_LABEL: Record<PaymentStatus, string> = {
  PAYMENT_PENDING: 'Ödeme Bekleniyor',
  PAID: 'Ödendi',
  REJECTED: 'Reddedildi',
  CANCELLED: 'İptal Edildi',
  REFUNDED: 'İade Edildi',
} as const;

export function PaymentStatusBadge({ status }: { readonly status: PaymentStatus }) {
  // KR-033: PAID yalnızca dekont + manuel onay + audit akışı sonunda olur.
  return <Badge variant={BADGE_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>;
}
