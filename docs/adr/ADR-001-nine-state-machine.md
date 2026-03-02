BOUND: TARLAANALIZ_SSOT_v1_0_0.txt – canonical rules are referenced, not duplicated.

# ADR-001: 9 Durumlu Dataset State Machine Kararı

## Durum
Kabul Edildi

## Tarih
2026-03-01

## Bağlam

Dataset lifecycle (KR-072) için 9 durumlu state machine ile 5 durumlu
sadeleştirilmiş alternatif değerlendirildi.

**Mevcut 9 durum (KR-072 kanonik):**
```
RAW_INGESTED → RAW_SCANNED_EDGE_OK → RAW_HASH_SEALED → CALIBRATED
→ CALIBRATED_SCANNED_CENTER_OK → DISPATCHED_TO_WORKER → ANALYZED
→ DERIVED_PUBLISHED → ARCHIVED
(herhangi bir aşamada hata → REJECTED_QUARANTINE)
```

**Önerilen 5 durumlu alternatif:**
```
RAW → VERIFIED → DISPATCHED → ANALYZED → PUBLISHED
```

## Karar

9 durum korunur. 5 duruma geçiş **reddedildi**.

## Gerekçe

1. **AV tarama katmanları ayrı güvenlik işlevi görür:**
   AV1 (Edge) ve AV2 (Merkez) farklı aşamalardır; birleştirmek
   "AV1 PASS ama AV2 FAIL" senaryosunun audit izini yok eder.

2. **KVKK denetim izi zorunluluğu:**
   Her aşamanın ayrı kayıt altında tutulması yasal gereklilik.
   5 durumlu modelde hangi kontrol noktasında hata oluştuğu belirsizleşir.

3. **Migration maliyeti:**
   Mevcut entegrasyonlar (contracts, workers, audit queries) 9 duruma
   bağlıdır. Geçiş tüm consumer'ları kırar.

## Sonuç

5 durumlu makine **v2.0'a kadar gündeme alınmaz**. Mevcut 9 durumlu
state machine KR-072'de kanonik olarak tanımlanmıştır.

## İlgili Maddeler
- [KR-072] Dataset Lifecycle + Chain of Custody
- [KR-073] Untrusted File Handling + AV1/AV2
- `docs/architecture/data_lifecycle_transfer.md` §2 Dataset Durum Makinesi
