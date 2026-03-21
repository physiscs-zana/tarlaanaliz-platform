/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Abonelik kart bileseni. */

"use client";

export interface SubscriptionData {
  subscription_id: string;
  field_name: string;
  crop_type: string;
  status: "ACTIVE" | "PAST_DUE" | "CANCELLED" | "PENDING";
  interval: "SEASONAL" | "MONTHLY" | "YEARLY";
  next_due: string | null;
}

export interface SubscriptionCardProps {
  subscription: SubscriptionData;
}

const statusConfig: Record<
  SubscriptionData["status"],
  { label: string; className: string }
> = {
  ACTIVE: {
    label: "Aktif",
    className: "bg-emerald-100 text-emerald-700",
  },
  PAST_DUE: {
    label: "Gecikmiş",
    className: "bg-amber-100 text-amber-700",
  },
  CANCELLED: {
    label: "İptal Edildi",
    className: "bg-rose-100 text-rose-700",
  },
  PENDING: {
    label: "Beklemede",
    className: "bg-slate-100 text-slate-600",
  },
};

const intervalLabel: Record<SubscriptionData["interval"], string> = {
  SEASONAL: "Sezonluk",
  MONTHLY: "Aylık",
  YEARLY: "Yıllık",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export function SubscriptionCard({ subscription }: SubscriptionCardProps) {
  const status = statusConfig[subscription.status];

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-slate-900">
            {subscription.field_name}
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            {subscription.crop_type}
          </p>
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${status.className}`}
        >
          {status.label}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-4 text-sm text-slate-600">
        <span>{intervalLabel[subscription.interval]}</span>
        {subscription.next_due && (
          <span>
            Sonraki ödeme: {formatDate(subscription.next_due)}
          </span>
        )}
      </div>
    </div>
  );
}
