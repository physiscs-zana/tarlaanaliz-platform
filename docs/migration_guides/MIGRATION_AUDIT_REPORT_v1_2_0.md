# Alembic Migration Denetim Raporu — SSOT v1.2.0

> BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

**Tarih:** 2026-03-05
**Denetim kapsamı:** 21 migration dosyası, alembic/env.py, alembic.ini
**SSOT versiyonu:** v1.2.0
**Denetim rolleri:** Kıdemli SDLC Uzmanı, Technical Writer / SSOT Custodian, Domain Expert (AgriTech), Data Engineer / Pipeline Architect, Security Architect, QA Engineer / Test Architect, Kıdemli Yazılım Mimarı ve Yazılım Mühendisi

---

## YONETICI OZETI

21 migration dosyasının SSOT v1.2.0'a karşı kapsamlı denetimi sonucunda **5 CRITICAL**, **7 MAJOR**, **5 RUNTIME FAIL** ve **12+ MINOR** bulgu tespit edilmiştir. Migration zinciri çalıştırılamaz durumdadır (branch fork + runtime failure). Aşağıda tüm bulgular, 8 uzman perspektifinden sınıflandırılmıştır.

---

## BOLUM 1: REVISION CHAIN (SDLC Uzmanı)

### Revizyon Zinciri

| Revizyon | Dosya | Revises |
|----------|-------|---------|
| `001` | `20260101_001_initial_users_roles.py` | None |
| `002` | `20260101_002_initial_fields_crops.py` | `001` |
| `003` | `20260101_003_initial_missions.py` | `002` |
| `004` | `20260102_004_subscriptions.py` | `003` |
| `005` | `20260102_005_pilots.py` | `004` |
| `006` | `20260102_006_experts.py` | `005` |
| `007` | `20260103_007_analysis_jobs.py` | `006` |
| `008` | `20260103_008_expert_reviews.py` | `007` |
| `009` | `20260104_009_weather_blocks.py` | `008` |
| `010` | `20260104_010_audit_logs.py` | `009` |
| `011` | `20260104_011_weekly_schedules.py` | `010` |
| `012` | `20260105_012_indexes_performance.py` | `011` |
| `013` | `20260105_013_full_text_search.py` | `012` |
| `kr033` | `20260129_kr033_payment_intents.py` | `013` |
| `kr082` | `20260201_kr082_calibration_qc_records.py` | `kr033` |
| `wbr001` | `20260204_add_weather_block_reports.py` | `kr082` |
| `kr015a_mission_segments` | `20260225_014_kr015_mission_segments.py` | `wbr001` |
| `kr015b_seasonal_reschedule_tokens` | `20260225_015_kr015_seasonal_reschedule_tokens.py` | `kr015a` |
| `kr015c_mission_schedule_fields` | `20260223_kr015c_mission_schedule_fields.py` | `kr015b` |
| `kr015_3a` | `20260302_simplify_weather_block_status.py` | **`wbr001`** |
| `kr011_ba` | `20260302_add_billing_admin_role.py` | `kr015_3a` |

### BULGU-01 — BRANCH FORK (CRITICAL)

**Dosya:** `20260302_simplify_weather_block_status.py:20` ve `20260225_014_kr015_mission_segments.py:12`
**Sorun:** İki migration (`kr015a_mission_segments` ve `kr015_3a`) aynı parent'a (`wbr001`) bağlanmış. Alembic `upgrade head` komutu branch fork nedeniyle **çalışmayı reddeder**.
**Olması gereken zincir:**
```
wbr001 → kr015a → kr015b → kr015c → kr015_3a → kr011_ba
```
**Düzeltme:** `20260302_simplify_weather_block_status.py:20` satırındaki `down_revision` değeri `"kr015c_mission_schedule_fields"` olarak güncellenmelidir.

### BULGU-02 — TUTARSIZ TARIH SIRASI (MINOR)

**Dosya:** `20260223_kr015c_mission_schedule_fields.py`
**Sorun:** Dosya tarihi (2026-02-23) parent'ı `kr015b`'nin dosya tarihinden (2026-02-25) **önce**. Kronolojik sıra bozuk. Migration dosya adlandırma konvansiyonu ihlal ediliyor.

---

## BOLUM 2: SSOT UYUMLULUK (Technical Writer / SSOT Custodian)

### BULGU-03 — EKSIK `datasets` TABLOSU ve DURUM MAKINESI (CRITICAL)

**KR referansı:** KR-072, ADR-001
**Sorun:** SSOT v1.2.0 ve ADR-001 tarafından zorunlu kılınan 9+1 durumlu dataset state machine için **hiçbir migration tanımlanmamış**.
**Gerekli durumlar:** RAW_INGESTED, RAW_SCANNED_EDGE_OK, RAW_HASH_SEALED, CALIBRATED, CALIBRATED_SCANNED_CENTER_OK, DISPATCHED_TO_WORKER, ANALYZED, DERIVED_PUBLISHED, ARCHIVED, REJECTED_QUARANTINE
**Etki:** Veri yaşam döngüsü izlenemiyor. KVKK denetim izi oluşturulamıyor. Chain-of-custody kanıt zinciri kırık.
**Aksiyon:** `datasets` tablosu ve `dataset_state` enum'u oluşturan yeni migration yazılmalı.

### BULGU-04 — EKSIK `layer_registry` TABLOSU (MAJOR)

**KR referansı:** KR-064, KR-084
**Sorun:** SSOT KR-064 şu katman tiplerini zorunlu kılar: HEALTH, WEED, DISEASE, PEST, FUNGUS, WATER_STRESS, N_STRESS, THERMAL_STRESS. Hiçbir migration bu tabloyu oluşturmuyor.
**Mevcut durum:** `analysis_results.layer_refs` JSONB sütunu var ancak yapılandırılmış katman tipi doğrulaması yok.
**Etki:** Katman tutarlılığı garanti edilemiyor. KR-084 THERMAL_STRESS desteği şemada mevcut değil.

### BULGU-05 — YANLIS ODEME DURUM MAKINESI (MAJOR)

**KR referansı:** KR-033
**Dosya:** `20260129_kr033_payment_intents.py:64-68`
**SSOT gerekliliği:** intent → receipt → pending_approval → approved/rejected → paid
**Mevcut CHECK constraint:**
```sql
status IN ('PAYMENT_PENDING', 'PAID', 'REJECTED', 'EXPIRED', 'CANCELLED', 'REFUNDED')
```
**Eksik durumlar:** `INTENT` (SSOT kanonik), `RECEIPT`, `PENDING_APPROVAL`, `APPROVED`
**Fazla/yanlış durum:** `PAYMENT_PENDING` (SSOT'ta yok, `INTENT` olmalı)
**Etki:** IBAN havale dekont onay akışı DB seviyesinde modellenemiyor. KR-033 hard gate'i (`PAID` olmadan ASSIGNED olamaz) ara durumlardan yoksun.

### BULGU-06 — STALE WEATHER_BLOCKS TABLOSU (MAJOR)

**KR referansı:** KR-015-3A
**Dosya:** `20260104_009_weather_blocks.py:25-31` ve `20260302_simplify_weather_block_status.py`
**Sorun:** `simplify_weather_block_status` migration'ı sadece `weather_block_reports` tablosunu düzeltiyor. Orijinal `weather_blocks` tablosu hala deprecated PENDING/VERIFIED/REJECTED enum'unu kullanıyor.
**SSOT gerekliliği:** REPORTED, RESOLVED, EXPIRED
**Etki:** İki weather tablosu çelişen durum makineleri kullanıyor. `weather_block_status` PostgreSQL enum tipi hiç güncellenmemiş.

### BULGU-07 — STALE ROL YORUMU (MINOR)

**Dosya:** `20260101_001_initial_users_roles.py:24`
**Sorun:** Yorum "12 kanonik rol" diyor, SSOT v1.2.0 13 rol tanımlıyor (BILLING_ADMIN dahil).

---

## BOLUM 3: RUNTIME FAIL BULGULARI (QA Engineer / Test Architect)

### BULGU-08 — CIFT TANIMLI SUTUNLAR (RUNTIME FAIL)

**Dosya:** `20260129_kr033_payment_intents.py:115-123` vs `20260101_003_initial_missions.py:71-74`
**Sorun:** `missions.payment_intent_id` sütunu migration 003'te (FK olmadan) oluşturuluyor, ardından kr033'te `op.add_column()` ile tekrar ekleniyor. PostgreSQL `column already exists` hatası verecektir.
**Aynı sorun:** `subscriptions.payment_intent_id` — migration 004:100-104'te oluşturuluyor, kr033:128-136'da tekrar ekleniyor.
**Düzeltme:** kr033'teki `op.add_column()` çağrıları `op.create_foreign_key()` ile değiştirilmeli (sütun zaten var, sadece FK eksik).

### BULGU-09 — HAYALET SUTUN INDEKSI: `missions.pilot_id` (RUNTIME FAIL)

**Dosya:** `20260105_012_indexes_performance.py:62-65`
**Sorun:** `idx_missions_pilot_status` indeksi `missions` tablosundaki `["pilot_id", "status"]` sütunlarına referans veriyor. Ancak `missions` tablosunda `pilot_id` sütunu **yok**. Pilot atamaları `mission_assignments` junction tablosunda tutuluyor.
**Düzeltme:** İndeks ya kaldırılmalı ya da `mission_assignments` tablosuna taşınmalı.

### BULGU-10 — HAYALET SUTUN INDEKSI: `fields.status` (RUNTIME FAIL)

**Dosya:** `20260105_012_indexes_performance.py:270`
**Sorun:** `idx_fields_user` indeksi `["user_id", "status"]` kullanıyor ancak `fields` tablosunda `status` sütunu yok (sadece `is_active` Boolean var).
**Düzeltme:** `"status"` yerine `"is_active"` kullanılmalı.

### BULGU-11 — HAYALET SUTUN INDEKSI: `fields.crop_type` (RUNTIME FAIL)

**Dosya:** `20260105_013_full_text_search.py:58-63`
**Sorun:** `idx_fields_crop_type_trgm` trigram GIN indeksi `fields.crop_type` sütununa referans veriyor. `fields` tablosunda `crop_type` sütunu yok — bitki türleri ayrı `field_crops` tablosunda tutuluyor.
**Düzeltme:** İndeks kaldırılmalı veya `field_crops.crop_type` üzerinde oluşturulmalı (enum tipinde trigram GIN kullanılamaz — bu indeks mantıksal olarak anlamsız).

### BULGU-12 — YANLIS SUTUN ADI: `audit_logs.created_at` (RUNTIME FAIL)

**Dosya:** `20260105_012_indexes_performance.py:176`
**Sorun:** `idx_audit_logs_event_type` indeksi `["event_type", created_at DESC]` kullanıyor. `audit_logs` tablosunda timestamp sütunu `ts` olarak adlandırılmış, `created_at` değil.
**Düzeltme:** `created_at DESC` yerine `ts DESC` kullanılmalı.

---

## BOLUM 4: CIFT INDEKS / PERFORMANS (Data Engineer / Pipeline Architect)

### BULGU-13 — ~18 CIFT TANIMLI INDEKS (MINOR ama PERFORMANS ETKILI)

**Dosya:** `20260105_012_indexes_performance.py` (passim)
**Sorun:** Migration 012, önceki migration'larda (003, 004, 007, 008, 009) zaten oluşturulmuş indeksleri farklı isimlerle (ix_ vs idx_ prefix) tekrar oluşturuyor. PostgreSQL aynı sütunlara iki ayrı B-Tree indeksi oluşturur.

| Migration 012 İndeksi | Zaten Var (Orijinal) |
|----------------------|---------------------|
| `idx_missions_status_due` (satır 33) | `ix_missions_status_due` (003:130) |
| `idx_missions_field_created` (satır 40) | `ix_missions_field_created` (003:131) |
| `idx_missions_subscription` (satır 47) | `ix_missions_subscription` (003:132) |
| `idx_missions_payment_intent` (satır 54) | `ix_missions_payment_intent` (003:133) |
| `idx_subscriptions_due` (satır 72) | `ix_subscriptions_due` (004:116) |
| `idx_subscriptions_field` (satır 79) | `ix_subscriptions_field` (004:117) |
| `idx_subscriptions_payment_intent` (satır 86) | `ix_subscriptions_payment_intent` (004:118) |
| `idx_analysis_jobs_mission` (satır 122) | `ix_analysis_jobs_mission` (007:122) |
| `idx_analysis_jobs_status` (satır 129) | `ix_analysis_jobs_status` (007:123) |
| `idx_analysis_results_mission` (satır 139) | `ix_analysis_results_mission` (007:156) |
| `idx_analysis_results_job` (satır 145) | `ix_analysis_results_job` (007:155) |
| `idx_expert_reviews_expert_status` (satır 156) | `ix_expert_reviews_expert` (008:124) |
| `idx_expert_reviews_mission` (satır 163) | `ix_expert_reviews_mission` (008:126) |
| `idx_feedback_grade` (satır 241) | `ix_feedback_grade` (008:177) |
| `idx_feedback_mission` (satır 247) | `ix_feedback_mission_created` (008:178) |
| `idx_route_files_parcel` (satır 313) | `ix_route_files_parcel` (003:154) |
| `idx_weather_blocks_mission` (satır 205) | `ix_weather_blocks_mission` (009:71) |
| `idx_weather_blocks_status` (satır 211) | `ix_weather_blocks_status` (009:73) |

**Etki:** Disk alanı israfı, INSERT/UPDATE performans düşüşü (her kayıt iki indeks günceller).
**Not:** Bazı çiftlerin sütun kompozisyonu küçük farklılıklar gösterir (ör. `idx_analysis_jobs_status` → `created_at DESC` vs `ix_analysis_jobs_status` → `queued_at`). Bu durumda her iki indeks ayrı ayrı gerekli olabilir ancak belgelenmeli.

### BULGU-14 — EKSIK FK INDEKSLERI (MEDIUM)

| Tablo | FK Sütunu | İndeks Durumu |
|-------|-----------|---------------|
| `pilot_earnings` | `mission_id` (005:156) | **EKSİK** — JOIN sorguları yavaş |
| `expert_reviews` | `escalated_to_expert_id` (008:121) | **EKSİK** — eskalasyon sorguları yavaş |
| `audit_logs` | `field_id`, `mission_id`, `job_id` | FK bile yok, soft reference (kasıtlı WORM tasarımı — kabul edilebilir) |

### BULGU-15 — JSONB SUTUNLARI GIN INDEKSI EKSIK (MEDIUM)

| Tablo | JSONB Sütunu | GIN İndeks |
|-------|-------------|-----------|
| `analysis_jobs` | `input_manifest` (007:116) | **EKSİK** |
| `analysis_jobs` | `output_manifest` (007:117) | **EKSİK** |
| `audit_logs` | `detail` (010:159) | **EKSİK** |
| `payment_intents` | `receipt_meta` (kr033:85) | **EKSİK** |
| `calibration_records` | `calibration_manifest` (kr082) | **EKSİK** |
| `qc_reports` | `flags` (kr082) | **EKSİK** |

### BULGU-16 — PARTITION STRATEJISI EKSIK (MEDIUM)

**Tablo:** `audit_logs`
**Sorun:** WORM (append-only) tablo sınırsız büyüyecek. Zaman bazlı partitioning stratejisi (RANGE by `ts`) tanımlanmamış.
**Öneri:** `PARTITION BY RANGE (date_trunc('month', ts))` ile aylık partition.

---

## BOLUM 5: GUVENLIK BULGULARI (Security Architect)

### BULGU-17 — ROW-LEVEL SECURITY (RLS) EKSIK (MAJOR)

**Sorun:** Hiçbir tabloda RLS politikası tanımlanmamış.
**Etki:** Uygulama katmanı devre dışı kalırsa tüm veriye erişim mümkün.
**Kritik tablolar:** `missions`, `analysis_results`, `expert_reviews`, `payment_intents`, `audit_logs`
**SSOT referansı:** KR-066 (KVKK), KR-063 (RBAC)

### BULGU-18 — ODEME VERILERI SIFRELEME EKSIK (MAJOR)

**Dosya:** `20260129_kr033_payment_intents.py:81-85`
**Sorun:** `provider_session_id`, `provider_payment_id`, `receipt_blob_id` düz metin olarak saklanıyor. PCI-DSS uyumluluğu için at-rest encryption gerekli.
**Öneri:** pgcrypto veya uygulama düzeyi şifreleme + `encryption_version` sütunu.

### BULGU-19 — ADMIN ROL DOGRULAMASI YOK (MEDIUM)

**Dosya:** `20260102_005_pilots.py:131` — `overridden_by` FK herhangi bir kullanıcıya işaret edebilir.
**Dosya:** `20260129_kr033_payment_intents.py:89` — `approved_by_admin_user_id` rol kontrolü yok.
**Sorun:** Veritabanı seviyesinde yetki doğrulaması yapılmıyor. Application bypass durumunda privilege escalation riski.

### BULGU-20 — CASCADE DELETE RISKLERI (MEDIUM)

| Tablo | FK | ondelete | Risk |
|-------|----|----------|------|
| `coop_memberships` (001:158) | `coop_id` | CASCADE | Kooperatif silinirse üyelik audit trail kaybı |
| `field_crops` (002:100) | `field_id` | CASCADE | Tarla silinirse bitki geçmişi kaybı |
| `user_roles` (001:78) | `user_id` | CASCADE | Kullanıcı silinirse rol atama geçmişi kaybı |

**Öneri:** Soft delete (is_deleted + deleted_at) veya ON DELETE RESTRICT tercih edilmeli.

### BULGU-21 — AUDIT LOG REFERANS BUTUNLUGU (MINOR)

**Dosya:** `20260104_010_audit_logs.py:145-149`
**Sorun:** `field_id`, `mission_id`, `job_id` sütunları FK constraint olmadan tanımlanmış. Silinen kayıtlara dangling reference oluşur.
**Not:** WORM tasarımı gereği bu kabul edilebilir — ancak belgelenmelidir.

### BULGU-22 — HARDCODED FALLBACK DB URL (MINOR)

**Dosya:** `alembic/env.py:59`
**Sorun:** `DATABASE_URL` yoksa `postgresql://localhost/tarlaanaliz` fallback değeri kullanılıyor.
**Risk:** Production ortamında yanlış veritabanına bağlanma.
**Öneri:** Fallback kaldırılmalı, `DATABASE_URL` zorunlu yapılmalı.

---

## BOLUM 6: DOMAIN-SPECIFIC BULGULAR (AgriTech Domain Expert)

### BULGU-23 — PostGIS SPATIAL INDEX EKSIK (MAJOR)

**Dosya:** `20260101_002_initial_fields_crops.py:71`
**Sorun:** `fields.boundary` (Geometry POLYGON SRID=4326) sütunu oluşturuluyor ancak **GIST spatial index** tanımlanmamış.
**Etki:** Spatial sorguları (ST_Contains, ST_Intersects, ST_Within) full table scan yapacak.
**Düzeltme:**
```sql
CREATE INDEX idx_fields_boundary_gist ON fields USING GIST (boundary);
```

### BULGU-24 — GEOMETRI VALIDASYONU YOK (MEDIUM)

**Dosya:** `20260101_002_initial_fields_crops.py:71`
**Sorun:** `ST_IsValid()` trigger veya CHECK constraint yok. Invalid polygon kabul edilebilir.
**AgriTech etkisi:** Self-intersecting polygon'lar alan hesaplamalarını bozar, drone rota planlamasında hata oluşturur.

### BULGU-25 — ALAN TUTARSIZLIK RISKI (MEDIUM)

**Dosya:** `20260101_002_initial_fields_crops.py:69-70`
**Sorun:** `area_m2` ve `area_donum` bağımsız saklanıyor. Tutarlılık kontrolü yok.
**1 dönüm ≈ 919.3 m²** — Değerler birbirinden sapabilir.
**Önerilen CHECK:**
```sql
CHECK (ABS(area_m2 - area_donum * 919.3) < area_m2 * 0.01)
```

### BULGU-26 — BITKI DEGISIM SEZONU KONTROLU EKSIK (MINOR)

**Dosya:** `20260101_002_initial_fields_crops.py:122`
**Sorun:** KR-013 kuralı: "yılda 1, 1 Ekim - 31 Aralık arası" bitki türü değişikliği. DB seviyesinde bu kural zorlanmıyor.

### BULGU-27 — `mission_segments.segment_no` UNIQUE CONSTRAINT EKSIK (MINOR)

**Dosya:** `20260225_014_kr015_mission_segments.py:33`
**Sorun:** `segment_no` Integer, ancak `(mission_id, segment_no)` UNIQUE constraint yok. Aynı mission'da mükerrer segment numaraları kabul edilir.

### BULGU-28 — `mission_assignments` CIFT ATAMA RISKI (MINOR)

**Dosya:** `20260102_005_pilots.py:102-134`
**Sorun:** `(pilot_id, mission_id)` için UNIQUE constraint yok (sadece `pilot_earnings` tablosunda `uq_pilot_earnings_pilot_mission` mevcut). Aynı pilot aynı mission'a birden fazla atanabilir.

---

## BOLUM 7: VERI BUTUNLUGU (Yazılım Mimarı)

### BULGU-29 — EKSIK CHECK CONSTRAINTS (MEDIUM)

| Tablo | Sütun | Eksik Kontrol |
|-------|-------|---------------|
| `subscriptions` (004:78-79) | `start_date`, `end_date` | `CHECK (start_date <= end_date)` |
| `fields` (002:69) | `area_m2` | `CHECK (area_m2 > 0)` |
| `fields` (002:70) | `area_donum` | `CHECK (area_donum > 0)` |
| `payment_intents` (kr033:54) | `amount_kurus` | `CHECK (amount_kurus > 0)` |
| `price_snapshots` (002:155) | `unit_price_kurus` | `CHECK (unit_price_kurus > 0)` |

### BULGU-30 — DOWNGRADE FONKSIYONLARI INCELEMESI (QA)

| Migration | Downgrade Durumu | Sorun |
|-----------|-----------------|-------|
| `kr011_ba` (BILLING_ADMIN) | `pass` (noop) | PostgreSQL enum'dan değer kaldırılamaz — kabul edilebilir ancak belgelenmeli |
| `kr015_3a` (weather status) | Veri kaybı riski | REPORTED → PENDING geri dönüşümde CONFIRMED/VERIFIED ayrımı kaybolmuş durumda |
| `010` (audit_logs) | Trigger/function drop ✓ | Doğru |
| `kr033` (payment_intents) | Sütun drop ✓ | Doğru, ancak BULGU-08'deki çift sütun sorunu downgrade'i de etkiler |

### BULGU-31 — `env.py` MODEL IMPORT FRAGILITY (MINOR)

**Dosya:** `alembic/env.py:38-43`
**Sorun:** `target_metadata` import hatası sessizce `None` yapılıyor. Autogenerate çalışmayacak ancak hata mesajı yok.
**Öneri:** En azından warning log eklemek.

---

## BOLUM 8: OZET TABLO (Severity Matrix)

| # | Severity | Kategori | Bulgu | Dosya:Satır |
|---|----------|----------|-------|-------------|
| 01 | **CRITICAL** | Chain | Branch fork: kr015_3a ve kr015a aynı parent | `simplify:20`, `014:12` |
| 03 | **CRITICAL** | KR-072 | datasets tablosu ve state machine tamamen eksik | — |
| 04 | **MAJOR** | KR-064/084 | layer_registry tablosu eksik | — |
| 05 | **MAJOR** | KR-033 | Ödeme durum makinesi SSOT'a uymuyor | `kr033:64-68` |
| 06 | **MAJOR** | KR-015-3A | weather_blocks tablosu hala deprecated enum kullanıyor | `009:25-31` |
| 08 | **RUNTIME** | Schema | payment_intent_id çift tanımlı (missions + subscriptions) | `kr033:115-136` |
| 09 | **RUNTIME** | Schema | missions.pilot_id sütunu yok ama indeks var | `012:62-65` |
| 10 | **RUNTIME** | Schema | fields.status sütunu yok ama indeks var | `012:270` |
| 11 | **RUNTIME** | Schema | fields.crop_type sütunu yok ama trigram indeks var | `013:58-63` |
| 12 | **RUNTIME** | Schema | audit_logs.created_at yok (ts kullanılmalı) | `012:176` |
| 13 | MINOR | Perf | ~18 çift tanımlı indeks (ix_ vs idx_) | `012` passim |
| 17 | **MAJOR** | Security | RLS politikası hiçbir tabloda yok | — |
| 18 | **MAJOR** | Security | Ödeme verileri şifrelenmemiş | `kr033:81-85` |
| 23 | **MAJOR** | PostGIS | GIST spatial indeks eksik | `002:71` |
| 14 | MEDIUM | Perf | FK sütunlarında indeks eksik | `005`, `008` |
| 15 | MEDIUM | Perf | JSONB sütunlarında GIN indeks eksik | `007`, `010`, `kr033`, `kr082` |
| 16 | MEDIUM | Perf | audit_logs partition stratejisi yok | `010` |
| 19 | MEDIUM | Security | Admin rol doğrulaması DB seviyesinde yok | `005:131`, `kr033:89` |
| 20 | MEDIUM | Security | CASCADE DELETE audit trail kaybı riski | `001:158`, `002:100` |
| 24 | MEDIUM | PostGIS | ST_IsValid() geometri doğrulaması yok | `002:71` |
| 25 | MEDIUM | Domain | area_m2 / area_donum tutarlılık kontrolü yok | `002:69-70` |
| 29 | MEDIUM | Integrity | Çeşitli CHECK constraint eksikleri | Çoklu |

---

## BOLUM 9: ONCELIKLI DUZELTME PLANI

### P0 — Blocker (Migration çalıştırılamaz)

1. **Branch fork düzeltmesi** — `kr015_3a.down_revision = "kr015c_mission_schedule_fields"`
2. **Çift sütun düzeltmesi** — kr033'te `op.add_column()` yerine `op.create_foreign_key()`
3. **Hayalet indeks düzeltmeleri** — 012 ve 013'teki 4 runtime fail indeksi

### P1 — SSOT Uyumsuzluk (Major gap)

4. **`datasets` tablosu + `dataset_state` enum** — KR-072 kanonik state machine
5. **`layer_registry` tablosu + `layer_type` enum** — KR-064 katman standardı
6. **Ödeme durum makinesi düzeltmesi** — KR-033 kanonik akışa uyum
7. **`weather_blocks` tablosu status düzeltmesi** — SSOT REPORTED/RESOLVED/EXPIRED

### P2 — Güvenlik ve Performans

8. **GIST spatial indeks** — fields.boundary
9. **RLS politikaları** — en azından missions, payment_intents, analysis_results
10. **Ödeme verisi şifreleme** — provider_session_id, provider_payment_id
11. **Çift indeks temizliği** — Migration 012'deki duplikasyonlar
12. **JSONB GIN indeksleri** — Tüm JSONB sütunları

### P3 — İyileştirme

13. CHECK constraint'ler (pozitif alan, tarih sırası)
14. FK indeksleri
15. Partition stratejisi (audit_logs)
16. Geometri validasyon trigger'ı

---

## BOLUM 10: TEST ALTYAPISI ve QA DEGERLENDIRMESI (QA Engineer / Test Architect)

### BULGU-32 — MIGRATION TESTI YOK (CRITICAL)

**Sorun:** Projede alembic migration'larını test eden hiçbir test dosyası bulunamadı.
**Detay:**
- `tests/` dizininde migration'a özel test dizini yok
- `tests/conftest.py` sadece domain fixture'ları yüklüyor
- `pyproject.toml` (145-161) test marker'ları tanımlıyor (unit, integration, e2e, performance) ancak database/migrations marker'ı yok
- `tests/unit/test_ssot_compliance_script.py` sadece SSOT uyumluluğunu test ediyor, migration'ları değil

**Önerilen testler:**
- `test_migration_chain`: Tüm revision'ların lineer bir zincir oluşturduğunu doğrular
- `test_upgrade_downgrade`: Her migration için upgrade/downgrade döngüsü (testcontainers ile)
- `test_ssot_enum_compliance`: Enum değerlerinin SSOT'taki kanonik listelerle eşleştiğini doğrular
- `test_no_duplicate_indexes`: Aynı sütun kombinasyonuna birden fazla indeks olmadığını doğrular
- `test_column_exists_for_index`: İndeks oluşturmadan önce sütunun varlığını kontrol eder
- `test_schema_consistency`: Uygulanan şemanın beklenen şemayla eşleştiğini doğrular

### BULGU-33 — CI/CD PIPELINE MIGRATION DOGRULAMASI YETERSIZ (CRITICAL)

**Dosya:** `.github/workflows/ci.yml:224-256`
**Sorun:** CI'daki `migration-check` job'ı yalnızca migration dosyalarını **listeliyor**. Gerçek doğrulama yapmıyor:
```python
# Mevcut doğrulama (satır 244-255):
files = [f for f in os.listdir(migration_dir) if f.endswith('.py')]
print(f'Found {len(files)} migration files')
```
**Yapılmayanlar:**
1. Migration'ları test veritabanına uygulamıyor
2. Migration syntax doğrulaması yok
3. `down_revision` zinciri kontrolü yok
4. Gerçek DB operasyonu çalıştırmıyor
5. Şema tutarlılığı doğrulaması yok

**Not:** `pyproject.toml` (satır 84) `testcontainers[postgres]` dev dependency olarak tanımlıyor ama CI workflow hiçbir zaman migration testi için database container başlatmıyor.

**Önerilen:** `alembic upgrade head` + `alembic downgrade base` + `alembic upgrade head` döngüsü testcontainers ile CI pipeline'ına eklenmeli.

### BULGU-34 — DOWNGRADE GUVENLIGI EKSIK (MAJOR)

**Kritik downgrade sorunları:**

| Migration | Dosya | Downgrade Durumu | Sorun |
|-----------|-------|-----------------|-------|
| `kr011_ba` | `20260302_add_billing_admin_role.py:28-31` | `pass` (boş) | PostgreSQL enum'dan değer kaldırılamıyor — `BILLING_ADMIN` downgrade sonrası kalır |
| `kr015_3a` | `20260302_simplify_weather_block_status.py:58-72` | Veri kaybı | `REPORTED → PENDING` geri dönüşümde `CONFIRMED`/`VERIFIED` ayrımı kaybolur |
| `013` | `20260105_013_full_text_search.py:122` | pg_trgm extension kalır | Extension DROP yorum satırında — güvenli ama eksik temizlik |

### BULGU-35 — IDEMPOTENCY SORUNLARI (MEDIUM)

**Sorunlu uygulamalar:**
- **Migration 012:** 25+ indeks oluşturma `IF NOT EXISTS` olmadan — kısmi hata sonrası yeniden çalıştırma crash eder
- **İyi uygulamalar:** Extension oluşturma (`CREATE EXTENSION IF NOT EXISTS`), enum oluşturma (`checkfirst=True`), downgrade'lerde `DROP TYPE IF EXISTS` kullanımı

### BULGU-36 — ROLLBACK PROSEDURU BELGELENMEMIS (CRITICAL)

**Sorun:** 21 migration için hiçbir rollback prosedürü belgelenmemiş.
**Detay:**
- `docs/migration_guides/README.md` sadece şablon içeriyor — gerçek prosedür yok
- Rollback şablonunda `1. ...` placeholder'ı var
- `scripts/backup_database.sh` (105 satır) mevcut ama deployment pipeline'ına entegre değil
- Staging deploy workflow'unda (`deploy-staging.yml`) migration çalıştırma adımı yok

**Önerilen:**
1. `docs/ROLLBACK.md` oluşturulmalı (enum downgrade, data recovery, şema doğrulama)
2. Backup scripti deployment pipeline'ına entegre edilmeli
3. Her migration için rollback uyarıları belgelenmeli

### BULGU-37 — DEPLOYMENT PIPELINE MIGRATION ADIMI EKSIK (MAJOR)

**Dosya:** `.github/workflows/deploy-staging.yml`
**Sorun:** Deployment workflow'unda `alembic upgrade head` çalıştırma adımı yok. Konteyner doğru şema versiyonu olmadan başlayabilir.
**Dosya:** `Dockerfile:45-47` — Alembic dosyaları kopyalanıyor ama otomatik migration çalıştırma yok:
```dockerfile
COPY alembic/ ./alembic/
COPY alembic.ini ./
```
**Önerilen:** Container başlangıcında şema versiyonu doğrulanmalı veya entrypoint'te `alembic upgrade head` çalıştırılmalı.

---

## BOLUM 11: 21 MIGRATION ENVANTER TABLOSU

| # | Revision | Dosya | Tarih | Up | Down | Notlar |
|---|----------|-------|-------|-----|------|--------|
| 1 | `001` | `20260101_001_initial_users_roles.py` | 2026-01-01 | ✓ | ✓ | users, roles, cooperatives; `checkfirst=True` |
| 2 | `002` | `20260101_002_initial_fields_crops.py` | 2026-01-01 | ✓ | ✓ | PostGIS, fields, field_crops, price_snapshots |
| 3 | `003` | `20260101_003_initial_missions.py` | 2026-01-01 | ✓ | ✓ | missions, route_files |
| 4 | `004` | `20260102_004_subscriptions.py` | 2026-01-02 | ✓ | ✓ | subscriptions, FK to missions |
| 5 | `005` | `20260102_005_pilots.py` | 2026-01-02 | ✓ | ✓ | pilots, assignments, earnings, crop_ops_profiles |
| 6 | `006` | `20260102_006_experts.py` | 2026-01-02 | ✓ | ✓ | experts, specializations, zone_authorities |
| 7 | `007` | `20260103_007_analysis_jobs.py` | 2026-01-03 | ✓ | ✓ | analysis_jobs, analysis_results |
| 8 | `008` | `20260103_008_expert_reviews.py` | 2026-01-03 | ✓ | ✓ | expert_reviews, feedback_records |
| 9 | `009` | `20260104_009_weather_blocks.py` | 2026-01-04 | ✓ | ✓ | weather_blocks (deprecated enum!) |
| 10 | `010` | `20260104_010_audit_logs.py` | 2026-01-04 | ✓ | ✓ | WORM audit_logs + immutability trigger |
| 11 | `011` | `20260104_011_weekly_schedules.py` | 2026-01-04 | ✓ | ✓ | weekly_schedules, schedule_entries, reschedule_logs |
| 12 | `012` | `20260105_012_indexes_performance.py` | 2026-01-05 | **FAIL** | ✓ | 5 RUNTIME FAIL (hayalet sütunlar); IF NOT EXISTS yok |
| 13 | `013` | `20260105_013_full_text_search.py` | 2026-01-05 | **FAIL** | ⚠ | crop_type trigram FAIL; pg_trgm extension downgrade atlanıyor |
| 14 | `kr033` | `20260129_kr033_payment_intents.py` | 2026-01-29 | **FAIL** | ✓ | Çift sütun tanımlama (payment_intent_id) |
| 15 | `kr082` | `20260201_kr082_calibration_qc_records.py` | 2026-02-01 | ✓ | ✓ | calibration_records, qc_reports |
| 16 | `wbr001` | `20260204_add_weather_block_reports.py` | 2026-02-04 | ✓ | ✓ | weather_block_reports |
| 17 | `kr015a` | `20260225_014_kr015_mission_segments.py` | 2026-02-25 | ✓ | ✓ | mission_segments scaffold |
| 18 | `kr015b` | `20260225_015_kr015_seasonal_reschedule_tokens.py` | 2026-02-25 | ✓ | ✓ | reschedule tokens, requests |
| 19 | `kr015c` | `20260223_kr015c_mission_schedule_fields.py` | 2026-02-23 | ✓ | ✓ | schedule_window, assignment_source |
| 20 | `kr015_3a` | `20260302_simplify_weather_block_status.py` | 2026-03-02 | ✓ | ⚠ | **BRANCH FORK!** Data migration + eksik downgrade |
| 21 | `kr011_ba` | `20260302_add_billing_admin_role.py` | 2026-03-02 | ✓ | ✗ | Enum ADD VALUE; downgrade `pass` |

**Lejant:** ✓ Doğru | ⚠ Kısmen sorunlu | ✗ Eksik/Boş | **FAIL** Runtime hatası verecek

---

## BOLUM 12: TOPLAM BULGU ISTATISTIKLERI

| Severity | Adet | Kategoriler |
|----------|------|-------------|
| **CRITICAL** | 7 | Branch fork, eksik datasets tablosu, migration testi yok, CI doğrulaması yetersiz, rollback prosedürü belgelenmemiş |
| **MAJOR** | 9 | Ödeme state machine, RLS eksik, layer_registry eksik, weather_blocks stale, PostGIS indeks eksik, şifreleme eksik, deployment pipeline eksik, downgrade güvenliği |
| **RUNTIME FAIL** | 5 | Çift sütun tanımlama (2), hayalet sütun indeksleri (3) |
| **MEDIUM** | 8 | FK indeksler, JSONB GIN indeksler, partition stratejisi, admin doğrulama, CASCADE riskleri, geometri validasyon, alan tutarlılığı, idempotency |
| **MINOR** | 8 | Stale yorum, tarih sırası, segment UNIQUE, çift atama, CHECK constraints, bitki sezonu, env.py fallback, audit referans |
| **TOPLAM** | **37** | |

---

**Rapor sonu.**
