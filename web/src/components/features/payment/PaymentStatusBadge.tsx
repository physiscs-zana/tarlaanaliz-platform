// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-033: PaymentIntent.status kanonik degerleri: PAYMENT_PENDING | PAID | REJECTED | CANCELLED | REFUNDED
import { Badge } from '@/components/ui/badge';

/** KR-033: Kanonik odeme durumu enum'u (SSOT ile birebir). */
export type PaymentStatus = 'PAYMENT_PENDING' | 'PAID' | 'REJECTED' | 'CANCELLED' | 'REFUNDED';

const BADGE_VARIANT: Record<PaymentStatus, 'default' | 'success' | 'warning' | 'danger' | 'info'> = {
  PAYMENT_PENDING: 'warning',
  PAID: 'success',
  REJECTED: 'danger',
  CANCELLED: 'default',
  REFUNDED: 'info',
} as const;

const STATUS_LABEL: Record<PaymentStatus, string> = {
  PAYMENT_PENDING: 'Ödeme Bekleniyor',
  PAID: 'Ödendi',
  REJECTED: 'Reddedildi',
  CANCELLED: 'İptal Edildi',
  REFUNDED: 'İade Edildi',
} as const;

/** KR-033: Her durum için kullanıcı bilgilendirme mesajı. */
const STATUS_DESCRIPTION: Record<PaymentStatus, string> = {
  PAYMENT_PENDING: 'Ödemeniz bekleniyor. Lütfen havale yapıp dekontu yükleyin.',
  PAID: 'Ödemeniz onaylandı. Analiz işlemi başlatılacaktır.',
  REJECTED: 'Ödemeniz reddedildi. Lütfen destek ile iletişime geçin.',
  CANCELLED: 'Ödeme iptal edildi. Yeni bir analiz talebi oluşturabilirsiniz.',
  REFUNDED: 'Ödemeniz iade edildi. Tutar hesabınıza yansıyacaktır.',
} as const;

export function PaymentStatusBadge({ status, showDescription = false }: { readonly status: PaymentStatus; readonly showDescription?: boolean }) {
  // KR-033: PAID yalnızca dekont + manuel onay + audit akışı sonunda olur.
  return (
    <div>
      <Badge variant={BADGE_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>
      {showDescription && (
        <p className="mt-1 text-xs text-slate-600">{STATUS_DESCRIPTION[status]}</p>
      )}
    </div>
  );
}
