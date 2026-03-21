/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Abonelik plan secim bileseni. */

"use client";

export interface SubscriptionPlan {
  plan_id: string;
  name: string;
  interval: "SEASONAL" | "MONTHLY" | "YEARLY";
  price_kurus: number;
  description?: string;
}

export interface SubscriptionPlanSelectorProps {
  plans: SubscriptionPlan[];
  selectedPlanId: string | null;
  onSelect: (planId: string) => void;
}

const intervalLabel: Record<SubscriptionPlan["interval"], string> = {
  SEASONAL: "Sezonluk",
  MONTHLY: "Aylık",
  YEARLY: "Yıllık",
};

function formatPrice(kurus: number): string {
  const lira = kurus / 100;
  return lira.toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
}

export function SubscriptionPlanSelector({
  plans,
  selectedPlanId,
  onSelect,
}: SubscriptionPlanSelectorProps) {
  if (plans.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 py-12 text-center">
        <p className="text-sm text-slate-500">Mevcut plan bulunamadı.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {plans.map((plan) => {
        const isSelected = plan.plan_id === selectedPlanId;
        return (
          <button
            key={plan.plan_id}
            type="button"
            onClick={() => onSelect(plan.plan_id)}
            className={`rounded-lg border-2 p-5 text-left transition hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
              isSelected
                ? "border-emerald-600 bg-emerald-50"
                : "border-slate-200 bg-white hover:border-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">
                {plan.name}
              </h3>
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
                {intervalLabel[plan.interval]}
              </span>
            </div>

            <p className="mt-3 text-2xl font-bold text-emerald-700">
              {formatPrice(plan.price_kurus)}
            </p>

            {plan.description && (
              <p className="mt-2 text-sm text-slate-500">{plan.description}</p>
            )}

            {isSelected && (
              <div className="mt-3 text-xs font-medium text-emerald-600">
                Secili plan
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
