/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Utility functions for formatting (phone, date, currency, area). */

/**
 * Format area from square meters to a human-readable string.
 * Shows hectares for large areas, dekar for medium, m² for small.
 */
export function formatArea(m2: number): string {
  if (m2 >= 10_000) {
    const ha = m2 / 10_000;
    return `${ha.toLocaleString("tr-TR", { maximumFractionDigits: 2 })} ha`;
  }
  if (m2 >= 1_000) {
    const dekar = m2 / 1_000;
    return `${dekar.toLocaleString("tr-TR", { maximumFractionDigits: 2 })} dönüm`;
  }
  return `${m2.toLocaleString("tr-TR", { maximumFractionDigits: 0 })} m²`;
}

/**
 * Format currency from kuruş (integer cents) to Turkish Lira string.
 */
export function formatCurrency(kurus: number): string {
  const lira = kurus / 100;
  return lira.toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
}

/**
 * Format an ISO date string to a localized Turkish date.
 */
export function formatDate(iso: string): string {
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

/**
 * Format a phone number for display.
 * Assumes Turkish phone format: 05XX XXX XX XX
 */
export function formatPhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");

  /* 10-digit national number: 5XX XXX XX XX */
  if (digits.length === 10) {
    return `0${digits.slice(0, 3)} ${digits.slice(3, 6)} ${digits.slice(6, 8)} ${digits.slice(8, 10)}`;
  }

  /* 11-digit with leading 0: 0 5XX XXX XX XX */
  if (digits.length === 11 && digits.startsWith("0")) {
    return `${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 9)} ${digits.slice(9, 11)}`;
  }

  /* 12-digit with country code 90: +90 5XX XXX XX XX */
  if (digits.length === 12 && digits.startsWith("90")) {
    return `+90 ${digits.slice(2, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10, 12)}`;
  }

  /* Fallback — return as-is */
  return phone;
}
