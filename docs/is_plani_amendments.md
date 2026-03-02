BOUND: TARLAANALIZ_SSOT_v1_0_0.txt – canonical rules are referenced, not duplicated.

# İş Planı Değişiklik Notları (Amendments)

> Bu doküman, `IS_PLANI_AKIS_DOKUMANI_v1_0_0.docx` dosyasına uygulanması
> gereken değişiklikleri listeler. .docx dosyası programatik olarak
> düzenlenemediğinden bu notlar referans amaçlıdır.

## Last updated
2026-03-02

---

## Değişiklik E — Bölüm 1.1 Rol Tablosuna 2 Satır

İş Planı Bölüm 1.1'deki rol tablosuna aşağıdaki 2 satır eklenecektir:

| Rol | Sorumluluk |
|-----|------------|
| İstasyon Operatörü (STATION_OPERATOR) | M1/M2 fiziksel operasyon yönetimi; PII görmez; analiz sonuçlarına erişim yok; EdgeKiosk bakım ve veri aktarım süreçlerini yürütür |
| Ödeme Yöneticisi (BILLING_ADMIN) | IBAN dekont onayı, geri ödeme işlemleri, İl Operatörü kar payı raporlama; 500 TL üstü işlemlerde CENTRAL_ADMIN'e eskalasyon zorunlu |

**SSOT referansı:** [KR-011], [KR-063]

---

## Değişiklik F — Bölüm 2.6'ya Operasyonel Politika Notu

İş Planı Bölüm 2.6'ya aşağıdaki operasyonel politika maddeleri eklenecektir:

### Ödeme Operasyonel Kuralları

1. **IBAN Onay SLA:** Havale/EFT ödemeleri için BILLING_ADMIN T+1 iş günü
   saat 17:00'ye kadar dekont kontrolünü tamamlar. Süre aşıldığında sistem
   otomatik uyarı üretir.

2. **Şüpheli Makbuz Eskalasyonu:** BILLING_ADMIN şüpheli veya tutarsız dekont
   tespit ettiğinde tek başına karar veremez. CENTRAL_ADMIN'e eskalasyon zorunludur.

3. **Geri Ödeme Limiti:** 500 TL altı geri ödemeler CENTRAL_ADMIN tek imza ile
   onaylanır. 500 TL ve üstü işlemler CENTRAL_ADMIN + BILLING_ADMIN ortak
   onayını gerektirir. Eşik değer konfigürasyonla yönetilir.

4. **İl Operatörü Kar Payı:** İl Operatörü gelir payı hesaplama ve ödeme
   mekanizması KR-083'te tanımlanmıştır (otomatik hesaplama, ayın ilk 7 günü
   ödeme, BILLING_ADMIN raporlar, CENTRAL_ADMIN onaylar).

**SSOT referansı:** [KR-033] §10, [KR-083]
