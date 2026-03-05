// BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
// KR-081: Contract-first schema gates.
// KR-050: Telefon + 6 haneli PIN validasyonu.
// KR-013: Tarla kayit alanlari validasyonu.

/** KR-050: Telefon numarasi — 10-15 rakam. */
export function isValidPhone(value: string): boolean {
  return /^\d{10,15}$/.test(value);
}

/** KR-050: PIN — tam 6 haneli sayisal. */
export function isValidPin(value: string): boolean {
  return /^\d{6}$/.test(value);
}

/** KR-013: Tarla alan degeri — pozitif sayi (m2). */
export function isValidArea(value: number): boolean {
  return Number.isFinite(value) && value > 0;
}

/** KR-013: Zorunlu metin alani — bos olmayan string. */
export function isRequiredText(value: string): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

/** KR-019: training_grade geçerlilik kontrolü. */
export function isValidTrainingGrade(value: string): boolean {
  return ['A', 'B', 'C', 'D', 'REJECT'].includes(value);
}

/** KR-019: grade_reason — max 200 karakter. */
export function isValidGradeReason(value: string): boolean {
  return typeof value === 'string' && value.trim().length > 0 && value.trim().length <= 200;
}

/** KR-033: Kanonik ödeme durumları. */
export function isValidPaymentStatus(value: string): boolean {
  return ['PAYMENT_PENDING', 'PAID', 'REJECTED', 'CANCELLED', 'REFUNDED'].includes(value);
}

/** KR-015-1: Günlük kapasite doğrulama (2500-3000 dönüm). */
export function isValidDailyCapacity(value: number): boolean {
  return Number.isFinite(value) && value >= 2500 && value <= 3000;
}

/** KR-015-1: Çalışma günü sayısı doğrulama (max 6). */
export function isValidWorkDays(count: number): boolean {
  return Number.isInteger(count) && count >= 1 && count <= 6;
}
