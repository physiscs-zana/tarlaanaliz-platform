BOUND: TARLAANALIZ_SSOT_v1_0_0.txt – canonical rules are referenced, not duplicated.

# Title
Runbook: Weather Block Rapor Prosedürü

## Scope
Pilot tarafından bildirilen uçuş engeli (weather block) durumunda raporlama, yeniden planlama ve audit adımlarını tanımlar.

KR-015-3A: Pilot sahada tek yetkili kişidir. Admin doğrulama akışı kaldırılmıştır.

## Owners
- Flight Ops Lead
- Scheduler Ops

## Last updated
2026-03-02

## SSOT references
- KR-015-3A (Pilot Uçuş Yetki Bildirimi — Basitleştirilmiş)
- KR-015-5 (Weather Block Force Majeure — Reschedule Token Tüketmez)

## Raporlama prosedürü
1. Pilot "uçuş yapılamaz" bildirimi yapar (mission_id, reason, date).
2. Sistem bildirimi kaydeder → görev otomatik ertelenir.
3. Audit log'a yazılır (reporter, timestamp, reason, etkilenen mission, yeni planlanan tarih).
4. O günün hakedişi ödenmez.
5. Çiftçinin reschedule_token hakkı tüketilmez (KR-015-5: force majeure).

## Yeniden planlama
- Sistem otomatik yeniden planlama yapar (KR-015-5).
- Yeni tarih çiftçiye bildirilir.
- Pilot yeni tarihe atanır (veya uygun başka pilot).

## False positive handling
- Kısa süreli anomalide bekleme penceresi uygula.
- Pilot hatalı bildirim yaptıysa: RESOLVED durumuna geçir, audit log'a not ekle.

## Audit fields
- mission_id
- reporter_id (pilot)
- reason
- date
- correlation_id

## Failure modes
- Pilot bildirimi sisteme ulaşmadı → retry mekanizması.
- Yeniden planlama başarısız → ops alarm.

## Checklists
### Preflight
- Pilot bildirim endpoint'i erişilebilir.
- Planner entegrasyonu aktif.

### Operate
- Bildirimler loglandı.
- Yeniden planlama başarı oranı izlendi.

### Postmortem
- Hatalı bildirimler analiz edildi.
- Yeniden planlama başarı oranı değerlendirildi.

## Related docs
- `docs/architecture/subscription_scheduler_design.md`
- `docs/views/VIEW_CAPABILITIES.md`
