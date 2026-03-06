# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

# TarlaAnaliz Platform — Derin Denetim Raporu v1.2.0

**Tarih:** 2026-03-06
**Kapsam:** Yalnızca platform tarafı (backend, persistence, API, pipeline orchestration, security)
**SSOT Referansı:** `docs/TARLAANALIZ_SSOT_v1_2_0.txt`
**Denetim Perspektifleri:** Kıdemli SDLC Uzmanı, Technical Writer / SSOT Custodian, Domain Expert (AgriTech), Data Engineer / Pipeline Architect, Security Architect, QA Engineer / Test Architect, Kıdemli Yazılım Mimarı, Yazılım Mühendisi

---

## Yönetici Özeti

Platform kod tabanı **SSOT v1.2.0** ile karşılaştırmalı derin denetime tabi tutulmuştur. Domain katmanı (entities, value objects, domain services) büyük ölçüde SSOT ile uyumludur. Ancak **altyapı katmanı (persistence/ORM) eksik**, **Alembic migration zinciri kırık** ve **SSOT'un kendisinde iç tutarsızlıklar** tespit edilmiştir.

**Genel Uyumluluk Skoru:** ~55/100 (domain katmanı ~85, persistence katmanı ~25, SSOT iç tutarlılık ~70)

---

## 1. KRİTİK BULGULAR (P0 — Acil Düzeltme Gerekli)

### 1.1 Alembic Migration Zinciri — Branch Fork (Data Engineer + SDLC Uzmanı)

**Sorun:** `wbr001` revision'ından iki ayrı dal çıkıyor:
- `wbr001` → `kr015a_mission_segments` → `kr015b_seasonal_reschedule_tokens` → `kr015c_mission_schedule_fields`
- `wbr001` → `kr015_3a` → `kr011_ba`

**Etki:** `alembic upgrade head` çalıştırılamaz; Alembic "multiple heads" hatası verir. Deployment pipeline tamamen durur.

**Çözüm:** İki dalı birleştiren bir merge migration oluşturulmalı:
```python
# alembic/versions/YYYYMMDD_merge_heads.py
revision = "merge_001"
down_revision = ("kr015c_mission_schedule_fields", "kr011_ba")
```

**İlgili KR:** KR-041 (CI Gate), Governance Pack §PR Gate

---

### 1.2 ORM Model Stub'ları — 11/13 Dosya Boş (Yazılım Mühendisi + Data Engineer)

**Sorun:** `src/infrastructure/persistence/sqlalchemy/models/` altında 13 model dosyasından **11'i TODO stub**:

| Dosya | Durum | İlgili KR |
|-------|-------|-----------|
| `analysis_job_model.py` | ✅ İmplemente | KR-017, KR-018 |
| `analysis_result_model.py` | ❌ Stub | KR-017, KR-081 |
| `audit_log_model.py` | ❌ Stub | KR-040, BÖLÜM 3 |
| `expert_model.py` | ❌ Stub | KR-019 |
| `expert_review_model.py` | ❌ Stub | KR-019, KR-029 |
| `field_model.py` | ❌ Stub | KR-013, KR-080 |
| `mission_model.py` | ❌ Stub | KR-028 |
| `payment_intent_model.py` | ❌ Stub | KR-033 |
| `pilot_model.py` | ❌ Stub | KR-015 |
| `price_snapshot_model.py` | ❌ Stub | KR-022 |
| `subscription_model.py` | ✅ İmplemente | KR-027 |
| `user_model.py` | ❌ Stub | KR-050, KR-063 |
| `weather_block_model.py` | ❌ Stub | KR-015-3A |

**Etki:** Domain katmanı eksiksiz çalışıyor ancak veritabanı ile bağlantı kurulamıyor. Alembic migration'lar ile ORM modelleri arasında autogenerate desteği kullanılamaz.

**Çözüm:** Her stub dosyası için ilgili Alembic migration'daki sütun tanımlarına ve domain entity'deki alanlara uygun SQLAlchemy model yazılmalı.

---

### 1.3 Eksik `datasets` Tablosu (Data Engineer + Security Architect)

**Sorun:** KR-072 kanonik 9 durumlu Dataset state machine domain katmanında tam olarak implemente edilmiş (`src/core/domain/entities/dataset.py`, `src/core/domain/value_objects/dataset_status.py`) ancak:
- Alembic migration'larda `datasets` tablosu **yok**
- `src/infrastructure/persistence/sqlalchemy/models/` altında `dataset_model.py` **yok**

**Etki:** Chain-of-custody (kanıt zinciri) veritabanında saklanamıyor. KR-072 gereksinimleri karşılanamaz.

**Çözüm:** `datasets` tablosu için Alembic migration + ORM model oluşturulmalı. Minimum sütunlar:
- `id` (UUID PK)
- `status` (enum: 10 durum, KR-072)
- `mission_id` (FK → missions)
- `manifest_hash_sha256` (text, NOT NULL)
- `available_bands` (text[] / JSONB)
- `av1_report_id`, `av2_report_id` (nullable FK)
- `calibration_record_id` (nullable FK)
- `created_at`, `updated_at`, `status_changed_at`

**İlgili KR:** KR-072, KR-073, KR-017, ADR-001

---

### 1.4 KR-033 EXPIRED Durum Uyumsuzluğu (SSOT Custodian + Domain Expert)

**Sorun:** Kod (`payment_status.py:31`) `EXPIRED` durumunu tanımlıyor ve "7 gün içinde ödeme gelmezse" otomatik geçiş uyguluyor. Ancak SSOT KR-033 açıkça şunu söylüyor:

> "Süre dolumu (Expire) politikası: Sistemde otomatik expire yoktur. PAYMENT_PENDING durumundaki intent'ler admin kararıyla CANCELLED yapılabilir."

**Etki:** Kod ile SSOT arasında semantik çelişki. SSOT, Türkiye saha koşullarındaki kooperatif onay süreçlerini gerekçe göstererek bilinçli olarak auto-expire'ı reddetmiş.

**Çözüm:** `PaymentStatus.EXPIRED` durumu koddan kaldırılmalı. PAYMENT_PENDING → admin CANCELLED akışı SSOT ile uyumlu.

---

## 2. BÜYÜK BULGULAR (P1 — Sprint İçinde Düzeltme)

### 2.1 KR-063 RBAC Tutarsızlığı — BILLING_ADMIN + FARMER_MEMBER (SSOT Custodian)

**Sorun (düzeltildi):** KR-063 RBAC tablosunda `BILLING_ADMIN` rolü eksikti; KR-011 ve KR-033 §10'da tanımlı olmasına rağmen.

**Durum:** Bu denetimde SSOT'a BILLING_ADMIN rolü eklendi (KR-063 tablosu güncellendi).

**Kod tarafı uyumsuzluk:** `role.py` (v1.1.0) BILLING_ADMIN ve FARMER_MEMBER rollerini "kaldırıldı" olarak işaretlemiş. Ancak SSOT v1.2.0:
- **BILLING_ADMIN:** KR-011, KR-033, KR-083'te aktif olarak referans veriliyor → Kodda geri eklenmeli
- **FARMER_MEMBER:** KR-063 tablosunda mevcut → Kodda geri eklenmeli

**Ayrıca:** `kr011_ba` migration BILLING_ADMIN'i `user_roles` enum'una ekliyor ama `role.py` kaldırmış → Migration ile kod çelişiyor.

**İlgili KR:** KR-063, KR-011, KR-033

---

### 2.2 Eksik `layer_registry` Tablosu (Data Engineer + Domain Expert)

**Sorun:** KR-064 Layer Registry (HEALTH, WEED, DISEASE, PEST, FUNGUS, WATER_STRESS, N_STRESS, THERMAL_STRESS) veritabanında tanımlı değil. Katman kodları, renk, desen, opaklık ve öncelik bilgileri yalnızca SSOT dokümanında var.

**Çözüm:** `layer_registry` seed tablosu veya config dosyası oluşturulmalı. PWA'da tutarlılık için API üzerinden sunulmalı.

---

### 2.3 Eksik RLS (Row-Level Security) Politikaları (Security Architect)

**Sorun:** `two_server_architecture.md` dosyasında `pipeline_rw` DB rolü tanımlanmış ve erişim matrisi belirlenmiş. Ancak Alembic migration'larda RLS policy'leri uygulanmamış.

**Etki:** Server 2 (Data Pipeline) `pipeline_rw` rolü ile `users`, `payment_intents`, `user_pii` gibi PII tablolarına erişebilir durumda. KR-066 ihlali.

**Çözüm:** PostgreSQL RLS policy migration'ı:
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY pipeline_deny ON users FOR ALL TO pipeline_rw USING (false);
```

---

### 2.4 PostGIS Spatial Index Eksikliği (Data Engineer)

**Sorun:** `fields` tablosunda `boundary` sütunu (Geometry/Geography) mevcut ama GIST indeks tanımlanmamış. KR-065 coverage ratio hesaplaması ve KR-016 eşleştirme performansı etkilenir.

**Çözüm:** Migration ile `CREATE INDEX idx_fields_boundary_gist ON fields USING GIST (boundary);`

---

### 2.5 Alembic Migration'larda Runtime Hataları (Data Engineer + QA Engineer)

Önceki denetim raporunda (`MIGRATION_AUDIT_REPORT_v1_2_0.md`) tespit edilen ve hâlâ düzeltilmemiş hatalar:

| Hata | Migration | Detay |
|------|-----------|-------|
| Duplicate `payment_intent_id` sütunu | `kr033` + `004` | `missions` ve `subscriptions` tablolarında çakışma |
| Phantom index referansları | `012` | `fields.pilot_id`, `fields.status`, `fields.crop_type` sütunları mevcut değil |
| Yanlış timestamp sütun adı | `010` | `audit_logs.timestamp` → `audit_logs.created_at` olmalı |

---

## 3. ORTA SEVİYE BULGULAR (P2 — Planlı İyileştirme)

### 3.1 CI/CD Pipeline'da Migration Test Eksikliği (SDLC Uzmanı + QA Engineer)

**Sorun:** `.github/workflows/` altında veya CI konfigürasyonunda Alembic migration chain validation testi yok. KR-041 (CI Gate) gereği:
- `alembic check` (multi-head detection)
- `alembic upgrade head` (execution test against test DB)
- `alembic downgrade -1` (reversibility test)

**Çözüm:** CI pipeline'a migration smoke test adımı eklenmeli.

---

### 3.2 Payment Data Encryption Durumu (Security Architect)

**Sorun:** `encryption.py` Fernet şifreleme implementasyonu mevcut. `user_pii.py:32` IBAN için `iban_encrypted` alanı var. Ancak:
- Kredi kartı verisi platformda saklanmıyor (doğru — hosted checkout modeli)
- IBAN verisi PII vault'a taşınmak yerine `user_pii` entity'sinde tutuluyor
- KR-033 "receipt_blob_id" opak referans olarak tanımlanmış ama blob'un nerede saklandığı belirtilmemiş

**Çözüm:** IBAN verisi için PII vault entegrasyonu ve blob storage referans dokümentasyonu.

---

### 3.3 BÖLÜM 3 Audit Log Eksiklikleri (SSOT Custodian — düzeltildi)

**Sorun:** WORM minimum olay seti KR-084 termal pipeline, KR-033 SLA ihlali ve KR-073 scan policy olaylarını içermiyordu.

**Durum:** Bu denetimde düzeltildi. Eklenen olaylar:
- `PAYMENT.SLA_BREACH`, `PAYMENT.ESCALATED`
- `THERMAL.PIPELINE_ACTIVATED`, `THERMAL.CALIBRATION_VERIFIED`, `THERMAL.QC_PASS/WARN/FAIL`, `THERMAL.RESULT_PUBLISHED`
- `SCAN_POLICY.BYPASS_ACTIVATED`, `SCAN_POLICY.BYPASS_EXTENDED`
- `PROVINCE_OPERATOR.RATE_CHANGED`

---

### 3.4 Subscription Model — reschedule_tokens Entegrasyonu (Domain Expert + QA)

**Sorun:** `subscription_model.py` implemente edilmiş ancak KR-015-5 `reschedule_tokens_per_season` alanı ile weather block force majeure entegrasyonu test edilmemiş. SSOT kuralı:

> "Hava engeli (Weather Block) / force majeure nedeniyle yapılan ertelemeler reschedule token tüketmez"

**Çözüm:** Entegrasyon testi: weather block → system_reschedule → token tüketilmediği doğrulanmalı.

---

## 4. DÜŞÜK SEVİYE BULGULAR (P3 — Backlog)

### 4.1 calibration_gate_service MIN_REQUIRED_BANDS Hardcoded (Yazılım Mimarı)

`calibration_gate_service.py:16` — `MIN_REQUIRED_BANDS = 4` sabit kodlanmış. `drone_model.py` veya `spectral_tier.py`'deki kanonik sabite referans verilmeli.

### 4.2 role.py BOUND Header — v1.1.0 Referansı (SSOT Custodian)

`role.py:1` `BOUND: TARLAANALIZ_SSOT_v1_1_0.txt` diyor. v1.2.0'a güncellenmeli.

### 4.3 Missing `drone_capability_matrix` Seed Data (Domain Expert + Data Engineer)

`config/drone_capability_matrix.yaml` dosyası mevcut ve doğru. Ancak bu verinin veritabanına seed edilmesi veya uygulama başlangıcında yüklenmesini sağlayan mekanizma test edilmemiş.

### 4.4 Expert Portal Notification Testi Eksik (QA Engineer)

KR-019 ve SC-EXP-01: Low confidence → expert review → SMS bildirimi zinciri end-to-end test edilmemiş.

### 4.5 Weather Block Enum Stale Değerleri (Data Engineer)

`009_weather_blocks.py` migration'ında tanımlanan weather_block_status enum'u (`PENDING`, `CONFIRMED`, `REJECTED`, `EXPIRED`) ile KR-015-3A sonrası basitleştirilmiş model (`REPORTED`, `EXPIRED`) arasında uyumsuzluk var. `kr015_3a` migration'ı düzeltme yapmış ama eski enum değerleri hâlâ mevcut.

---

## 5. UZMAN PERSPEKTİFLERİ — PLATFORM ODAKLI DETAY

### 5.1 Kıdemli SDLC Uzmanı

**Güçlü Yönler:**
- Clean architecture katmanlama disiplini mükemmel (core → application → infrastructure)
- Domain events pattern tutarlı uygulanmış
- BOUND header convention dosya izlenebilirliğini sağlıyor

**Zayıf Yönler:**
- Alembic migration chain kırık (P0)
- CI/CD'de migration validation yok
- Breaking-change detector CI step'i henüz implemente değil

### 5.2 Technical Writer / SSOT Custodian

**Güçlü Yönler:**
- KR şablonu tutarlı uygulanmış (Amaç → Kapsam → Zorunluluklar → Kanıt → Test)
- Cross-reference disiplini yüksek
- ADR-001 ve ADR-002 karar gerekçeleri detaylı

**Düzeltilen Sorunlar (bu denetimde):**
- KR-063'e BILLING_ADMIN eklendi
- BÖLÜM 3 audit log setine 10 eksik olay eklendi
- BÖLÜM 5 navigasyonuna ADR ve eksik KR referansları eklendi
- KR-033 §8 audit log tablosuna PAYMENT.SLA_BREACH ve PAYMENT.ESCALATED eklendi

### 5.3 Domain Expert (AgriTech)

**Güçlü Yönler:**
- Graceful degradation (4 bant → 5 bant → termal) modeli tarım gerçeklerine uygun
- DJI Mavic 3M radyometri notu doğru ve kapsamlı
- CropOpsProfile bitki türü bazlı kapasite profili iyi tasarlanmış
- drone_capability_matrix.yaml sensör bazlı bant/indeks eşlemesi eksiksiz

**Dikkat Edilmesi Gerekenler:**
- Red Edge bant pozisyonu farkı (730 nm vs 715 nm) offset katsayısı drone_capability_matrix'te tanımlı — Worker'da uygulandığı doğrulanmalı
- Termal pipeline CWSI 0.0-1.0 aralığı iyi tanımlanmış; ancak bitki türü bazlı stres eşikleri henüz belirlenmemiş (pamuk vs buğday vs mısır farklı stres profilleri)

### 5.4 Data Engineer / Pipeline Architect

**Güçlü Yönler:**
- Dataset 9-state machine domain'de tam implemente
- Transfer batch resumable/chunk tasarımı doğru
- Correlation ID propagation standardı iyi tanımlanmış

**Kritik Eksikler:**
- `datasets` tablosu hiç oluşturulmamış (P0)
- Migration chain fork → deployment blocker (P0)
- RLS policy eksik → PII izolasyon riski (P1)
- PostGIS GIST index eksik → spatial query performans sorunu (P1)

### 5.5 Security Architect

**Güçlü Yönler:**
- mTLS cihaz kimliği implementasyonu (`mtls_verifier.py`)
- AV scan mode (SMART/BYPASS) KR-073 ile tam uyumlu
- PII filter middleware mevcut
- Rate limiting + anomaly detection middleware'leri implemente

**Kritik Eksikler:**
- RLS policy'leri uygulanmamış → pipeline_rw rolü PII tablolarına erişebilir
- WORM audit log modeli stub → immutable log garantisi sağlanamıyor
- Secret rotation mekanizması test edilmemiş (KR-041 Ops Checklist)

### 5.6 QA Engineer / Test Architect

**Güçlü Yönler:**
- Test senaryoları (BÖLÜM 6) kapsamlı tanımlanmış
- Coverage ratio threshold testleri domain'de mevcut
- Weather block force majeure testi planlanmış

**Eksikler:**
- Alembic migration chain testi yok → CI'da migration smoke test eklenmeli
- ORM model stub'ları nedeniyle integration testler çalışamıyor
- SC-01 (normal ingest) E2E test coverage eksik
- PaymentStateMachine EXPIRED state testi var ama SSOT'ta tanımlı değil → test yanlış spec'e yazılmış

### 5.7 Kıdemli Yazılım Mimarı

**Güçlü Yönler:**
- Clean architecture katman kuralları (`core` → `application` → `infrastructure`) doğru uygulanmış
- Port/adapter pattern tutarlı (18 repository port + implementation çifti)
- Domain events ile event-driven decoupling sağlanmış
- Value objects immutable (frozen=True dataclass) ve iş kuralları doğru encapsulate edilmiş

**Mimari Endişeler:**
- Infrastructure models stub olması nedeniyle clean architecture'ın "infrastructure implements ports" kuralı havada kalıyor
- `models.py` (toplam model dosyası) stub → SQLAlchemy Base metadata autogenerate desteği çalışmıyor
- Dual model structure (domain entity + ORM model) doğru pattern ama 11 stub nedeniyle mapping katmanı eksik

### 5.8 Yazılım Mühendisi

**Güçlü Yönler:**
- Kod kalitesi yüksek; type hints, docstrings, BOUND headers tutarlı
- Domain value objects iş kurallarını iyi encapsulate ediyor
- band_compliance_checker, calibration_gate_service, qc_gate_service SSOT ile birebir uyumlu
- Event-driven architecture (RabbitMQ publisher/consumer) implemente

**Teknik Borç:**
- 11 ORM model stub'ı → persistence katmanı fonksiyonel değil
- Alembic env.py target_metadata → models.py stub olduğu için autogenerate çalışmıyor
- Some repository implementations (dataset_repository_impl, calibration_record_repository_impl) muhtemelen stub — doğrulanmalı

---

## 6. SSOT DEĞİŞİKLİK ÖZETİ (Bu Denetimde Yapılan)

| Değişiklik | Yer | Gerekçe |
|------------|-----|---------|
| BILLING_ADMIN rolü eklendi | KR-063 RBAC tablosu | KR-011 ve KR-033 §10 ile tutarlılık |
| 10 audit olayı eklendi | BÖLÜM 3 WORM minimum seti | KR-084, KR-033, KR-073, KR-083 olayları eksikti |
| PAYMENT.SLA_BREACH + PAYMENT.ESCALATED eklendi | KR-033 §8 audit log tablosu | §10'da tanımlı olaylar §8'de yoktu |
| ADR + eksik KR referansları eklendi | BÖLÜM 5 navigasyon | Navigasyon eksikliklerinin giderilmesi |
| Denetim raporu referansı eklendi | BÖLÜM 5 | Bu raporun SSOT'tan erişilebilir olması |

---

## 7. ÖNCELİKLENDİRİLMİŞ AKSİYON PLANI

| Öncelik | Aksyon | Tahmini Etki | İlgili KR |
|---------|--------|-------------|-----------|
| **P0** | Alembic branch fork düzelt (merge migration) | Deployment blocker | KR-041 |
| **P0** | `datasets` tablosu + model oluştur | Chain-of-custody eksik | KR-072 |
| **P0** | 11 ORM model stub'ını implemente et | Persistence katmanı çalışmıyor | Tümü |
| **P0** | `EXPIRED` durumunu koddan kaldır | SSOT-Kod uyumsuzluğu | KR-033 |
| **P1** | BILLING_ADMIN + FARMER_MEMBER rolleri koda geri ekle | SSOT-Kod uyumsuzluğu | KR-063 |
| **P1** | RLS policy migration'ı | PII izolasyon riski | KR-066, KR-070 |
| **P1** | PostGIS GIST index | Spatial query performansı | KR-065, KR-016 |
| **P1** | `layer_registry` tablosu/config | PWA katman tutarlılığı | KR-064 |
| **P2** | CI migration smoke test | Regression koruması | KR-041 |
| **P2** | PII vault entegrasyonu | IBAN güvenliği | KR-066 |
| **P2** | reschedule_tokens integration test | Force majeure doğrulama | KR-015-5 |
| **P3** | role.py BOUND header v1.2.0 güncelle | Doküman izlenebilirliği | — |
| **P3** | MIN_REQUIRED_BANDS kanonik referans | Bakım kolaylığı | KR-018 |
| **P3** | Bitki türü bazlı termal stres eşikleri | Analiz kalitesi | KR-084 |

---

## 8. SONUÇ

Platform domain katmanı SSOT v1.2.0 ile yüksek oranda uyumludur. KR-018/KR-082 graceful degradation, KR-072 dataset state machine, KR-073 AV scan policy, KR-033 payment state machine domain'de doğru şekilde implemente edilmiştir.

Ancak **persistence katmanı büyük ölçüde eksiktir** (11/13 ORM model stub), **Alembic migration zinciri kırıktır** (branch fork → deployment blocker) ve **SSOT'un kendisinde düzeltilmesi gereken iç tutarsızlıklar** bulunmuştur (bu denetimde 4 tanesi düzeltilmiştir).

En kritik adım: **P0 aksiyonlarının hemen ele alınmasıdır.** Bunlar olmadan platform deploy edilemez ve E2E testler çalışamaz.
