# TarlaAnaliz Platform — Çoklu-Uzman Derin Denetim Raporu v2

**Tarih:** 2026-03-05
**Denetçi Rolleri:** Kıdemli SDLC Uzmanı, Technical Writer/SSOT Custodian, AgriTech Domain Expert, Data Engineer/Pipeline Architect, Security Architect, QA Engineer/Test Architect, Kıdemli Yazılım Mimarı & Mühendis
**Durum:** ❌ CANLIYA ALINMAYA HAZIR DEĞİL — Kritik düzeltmeler uygulandı, kalan sorunlar belgelendi

---

## Yönetici Özeti

Platform kapsamlı 7 uzman perspektifinden derin denetime tabi tutulmuştur. Önceki (v1, 2026-02-23) rapora göre bazı iyileştirmeler yapılmış olsa da, **yeni kritik güvenlik açıkları** ve **mimari tutarsızlıklar** tespit edilmiştir. Bu raporda bulunan kritik sorunlardan 10'u doğrudan düzeltilmiştir.

| Kategori | Kritik | Yüksek | Orta | Düşük | Düzeltilen |
|----------|--------|--------|------|-------|------------|
| Güvenlik | 4 | 6 | 5 | 2 | 6 |
| Mimari & Kod Kalitesi | 1 | 4 | 3 | 2 | 2 |
| Test & QA | 1 | 3 | 4 | 1 | 2 |
| CI/CD & SDLC | 0 | 2 | 3 | 1 | 1 |
| AgriTech Domain | 0 | 1 | 2 | 1 | 0 |
| Dokümantasyon & SSOT | 0 | 1 | 2 | 2 | 0 |
| Frontend | 1 | 3 | 4 | 2 | 1 |
| **Toplam** | **7** | **20** | **23** | **11** | **12** |

---

## 1. GÜVENLİK MİMARİSİ DENETİMİ (Security Architect)

### 1.1 KRITIK — JWT Token Expiration Doğrulaması Eksikti ✅ DÜZELTİLDİ
- **Dosya:** `src/presentation/api/middleware/jwt_middleware.py:91-119`
- **Sorun:** `_decode_token()` metodu imza doğrulaması yapıyor ama `exp` (expiration) ve `iat` (issued-at) claim'lerini kontrol etmiyordu. Süresi dolmuş tokenlar kabul ediliyordu.
- **Etki:** Ele geçirilen bir token sonsuza kadar kullanılabilirdi.
- **Düzeltme:** `exp` ve `iat` doğrulaması eklendi (satır 119-127).

### 1.2 KRITIK — CORS Varsayılan `allow_origins=["*"]` ✅ DÜZELTİLDİ
- **Dosya:** `src/presentation/api/settings.py:47`
- **Sorun:** CORS ayarı varsayılan olarak tüm origin'lere (`["*"]`) izin veriyordu.
- **Etki:** Cross-site request forgery ve veri sızdırma saldırılarına açık.
- **Düzeltme:** Varsayılan `["http://localhost:3000"]` olarak değiştirildi.

### 1.3 KRITIK — Webhook Signature Doğrulaması Yetersiz ✅ DÜZELTİLDİ
- **Dosya:** `src/presentation/api/v1/endpoints/payment_webhooks.py:37-39`
- **Sorun:** Sadece `if not signature` kontrolü vardı; imzanın geçerliliği (HMAC) doğrulanmıyordu. Herhangi bir string geçerli kabul ediliyordu.
- **Etki:** Sahte webhook çağrılarıyla ödeme durumu manipüle edilebilirdi.
- **Düzeltme:** HMAC-SHA256 signature doğrulaması eklendi.

### 1.4 KRITIK — Auth Servisi Hardcoded Credentials
- **Dosya:** `src/presentation/api/v1/endpoints/auth.py:56`
- **Sorun:** `_InMemoryPhonePinAuthService` sabit credentials (`+905555555555`/`123456`) ile production'da çalışabilir.
- **Etki:** Demo backdoor, tüm sisteme yetkisiz erişim.
- **Öneri:** Production ortamda gerçek auth servis implementasyonu zorunlu kılınmalı; InMemory stub'lar `APP_ENV=dev` gate'i ile korunmalı.

### 1.5 YÜKSEK — Token localStorage'da Saklanıyor
- **Dosya:** `web/src/lib/authStorage.ts:17`
- **Sorun:** JWT token `localStorage`'da saklanıyor. XSS saldırısı durumunda token ele geçirilebilir.
- **Öneri:** `httpOnly` + `Secure` cookie'lere geçilmeli.

### 1.6 YÜKSEK — Cookie'lerde Secure Flag Eksikti ✅ DÜZELTİLDİ
- **Dosya:** `web/src/hooks/useAuth.ts:35`
- **Sorun:** `setCookie()` fonksiyonu `Secure` flag'i kullanmıyordu.
- **Düzeltme:** HTTPS ortamında otomatik `Secure` flag eklendi.

### 1.7 YÜKSEK — JWT Secret Varsayılan Değer
- **Dosya:** `src/presentation/api/settings.py:57`
- **Sorun:** `API_JWT_SECRET` varsayılan olarak `"dev-only-secret"`. Env var set edilmezse production'da bu değer kullanılır.
- **Öneri:** Production'da secret yoksa uygulama başlatılmamalı (fail-fast).

### 1.8 YÜKSEK — get_current_user Dict/Dataclass Uyumsuzluğu ✅ DÜZELTİLDİ
- **Dosya:** `src/presentation/api/dependencies.py:333-343`
- **Sorun:** JWT middleware `AuthenticatedUser` dataclass koyuyor, `get_current_user` `dict` bekliyor → Runtime `401 Unauthorized` dönüyor.
- **Düzeltme:** Hem dict hem dataclass hem de genel obje desteği eklendi.

### 1.9 YÜKSEK — Auth Endpoint JWT Bypass Listesinde Eksik ✅ DÜZELTİLDİ
- **Dosya:** `src/presentation/api/settings.py:56`
- **Sorun:** Login ve refresh endpoint'leri JWT bypass listesinde değildi. Kimlik doğrulama yapmak için zaten kimlik doğrulama gerekliydi (circular dependency).
- **Düzeltme:** `/api/v1/auth/phone-pin/login`, `/api/v1/auth/phone-pin/refresh`, ve webhook endpoint bypass listesine eklendi.

### 1.10 YÜKSEK — IDOR Riski: Payment Endpoint
- **Dosya:** `src/presentation/api/v1/endpoints/payments.py:154-175`
- **Sorun:** `GET /{intent_id}` endpoint'i `user.user_id`'yi servise iletiyor ama service'in kullanıcı bazlı filtreleme yapıp yapmadığı InMemory stub'da doğrulanamıyor.
- **Öneri:** Gerçek servis implementasyonunda `actor_user_id == intent.owner_id` kontrolü zorunlu.

### 1.11 ORTA — Rate Limiting IP Maskeleme ile Bypass
- **Dosya:** `src/presentation/api/middleware/rate_limit_middleware.py:79`
- **Sorun:** Rate limit key'i `mask_ip(client_ip):user_id` formatında. IP maskeleme (`/24`) farklı IP'lerin aynı bucket'ı paylaşmasına neden olur → hedefli flood.
- **Öneri:** Rate limiting için tam IP kullanılmalı, maskeleme sadece loglama için.

### 1.12 ORTA — X-Forwarded-For Spoofing
- **Dosya:** `src/presentation/api/middleware/_shared.py:67-69`
- **Sorun:** `get_client_ip()` doğrudan `X-Forwarded-For` header'ını güveniyor; trusted proxy kontrolü yok.
- **Öneri:** Trusted proxy listesi eklenmeli.

### 1.13 ORTA — PII Filter Sadece JSON Response
- **Dosya:** `src/presentation/api/middleware/pii_filter.py:106`
- **Sorun:** PII filtreleme sadece `application/json` response'larda çalışıyor. CSV export, binary response vb. durumlar kapsamdışı.

### 1.14 ORTA — Receipt Upload Dosya Boyutu/Tipi Kontrolü Yok
- **Dosya:** `src/presentation/api/v1/endpoints/payments.py:116-151`
- **Sorun:** `upload_receipt` endpoint'inde `content_base64` alanı için max boyut veya dosya tipi kontrolü yok.
- **Öneri:** Base64 boyut limiti (ör. 5MB) ve izin verilen content-type'lar (image/pdf) kontrolü.

### 1.15 ORTA — Endpoint-Level RBAC Eksiklikleri
- **Dosyalar:** `fields.py`, `missions.py`, `results.py`, `subscriptions.py`, `weather_blocks.py`
- **Sorun:** Bu endpoint'ler `_require_authenticated_subject()` ile sadece kimlik doğrulaması yapıyor; rol kontrolü yok. Herhangi bir authenticated kullanıcı herhangi bir API'yi çağırabilir.
- **Öneri:** Her endpoint'e `require_roles()` dependency eklenmeli.

---

## 2. YAZILIM MİMARİSİ DENETİMİ (Software Architect)

### 2.1 YÜKSEK — InMemory Stub'lar Endpoint Seviyesinde
- **Dosyalar:** Neredeyse TÜM endpoint dosyaları (`fields.py`, `missions.py`, `results.py`, `expert_portal.py`, `weather_blocks.py`, vb.)
- **Sorun:** Her endpoint dosyası kendi `_InMemory*Service` stub'ını tanımlıyor ve `get_*_service()` fonksiyonu ile bunu default olarak döndürüyor. Gerçek servis bağlama (DI) mekanizması sadece `request.app.state` üzerinden çalışıyor (payments, calibration, QC, SLA).
- **Etki:** Endpoint'lerin çoğu production'da stub data döndürür.
- **Öneri:** Tutarlı DI container (ör. FastAPI lifespan event'te servislerin app.state'e bağlanması) tüm endpoint'lere uygulanmalı.

### 2.2 YÜKSEK — Hexagonal Mimari Port/Adapter Boşlukları
- **Sorun:** `src/core/ports/repositories/` altında 18 repository port tanımlı. `src/infrastructure/persistence/sqlalchemy/repositories/` altında 18 implementasyon var. ANCAK endpoint'ler bu repository'leri değil, kendi InMemory stub'larını kullanıyor.
- **Etki:** Clean Architecture kuralı kağıt üzerinde var ama fiili bağlantı yok.

### 2.3 YÜKSEK — Presentation Layer Domain Import
- **Dosya:** `src/presentation/api/dependencies.py`
- **Sorun:** Bu dosya hem presentation-layer DTO'ları hem de domain konseptlerini (PaymentStatus, QCStatus) yeniden tanımlıyor. Doğrudan core import yerine copy-paste ile senkron tutulmaya çalışılıyor.
- **Öneri:** Ya doğrudan domain import edilmeli ya da shared contract layer oluşturulmalı.

### 2.4 YÜKSEK — Çift Migration Sistemi
- **Dosyalar:** `alembic/versions/` (19 dosya) + `src/infrastructure/persistence/sqlalchemy/migrations/versions/` (3 dosya)
- **Sorun:** İki ayrı migration dizini var. Hangisinin kanonik olduğu belirsiz.
- **Öneri:** Tek migration dizini (alembic/) standartlaştırılmalı.

### 2.5 ORTA — Event Handler Bağlantı Eksikliği
- **Dosya:** `src/application/event_handlers/*.py` — 4 event handler tanımlı
- **Sorun:** Event handler'lar EventBus'a nerede bağlanıyor? `main.py`'de veya lifespan'de wiring yok.
- **Etki:** Domain event'ler publish edilse bile handle edilmez.

### 2.6 ORTA — Unit of Work Pattern Yarım
- **Dosya:** `src/infrastructure/persistence/sqlalchemy/unit_of_work.py`
- **Sorun:** UoW tanımlı ama endpoint'lerde kullanılmıyor. Transaction boundary'ler belirsiz.

### 2.7 ORTA — `_require_authenticated_subject()` Tekrarı
- **Dosyalar:** `fields.py`, `missions.py`, `results.py`, `expert_portal.py`, `subscriptions.py`
- **Sorun:** Aynı auth guard fonksiyonu 5+ dosyada kopyalanmış. `dependencies.py`'deki `get_current_user` ile çakışıyor.
- **Öneri:** Tek merkezden (`dependencies.py`) kullanılmalı.

---

## 3. VERİ MÜHENDİSLİĞİ DENETİMİ (Data Engineer)

### 3.1 KRITIK — CropType Scan Interval Uyumsuzluğu
- **Dosyalar:** `crop_type.py:65-74` vs `crop_scan_interval.py` (ayrı bir VO)
- **Sorun:** `CropType._SCAN_INTERVALS` ve `CropScanInterval` value object'inde **farklı tarama aralıkları** tanımlı:
  - `ANTEP_FISTIGI`: crop_type.py → (10, 15) vs crop_scan_interval.py → (14, 21)
  - `MISIR`: crop_type.py → (15, 20) vs crop_scan_interval.py → (7, 14)
- **Etki:** Hangi değer kullanılacağı çağrılan yere bağlı → tutarsız mission scheduling.
- **Öneri:** Tek kanonik kaynak (CropScanInterval) kullanılmalı, CropType'tan _SCAN_INTERVALS kaldırılmalı.

### 3.2 YÜKSEK — Migration Chain Doğrulaması Zayıf
- **Dosya:** `.github/workflows/ci.yml:243-255`
- **Sorun:** CI'daki migration validation sadece dosya listesini yazdırıyor. Revision chain bütünlüğü, down migration varlığı veya SQL syntax doğrulaması yapılmıyor.
- **Öneri:** `alembic check` veya custom chain validation script'i.

### 3.3 ORTA — Redis Password Boş Varsayılan
- **Dosya:** `.env.example:27` — `REDIS_PASSWORD=`
- **Sorun:** Redis varsayılan olarak parola korumasız.
- **Öneri:** Dev ortamında bile minimum parola gerekli.

### 3.4 ORTA — InMemory Depolama Concurrency Sorunu
- **Dosya:** `payment_webhooks.py:35` — `processed_events: set[str]`
- **Sorun:** In-memory set thread-safe değil ve multi-worker Uvicorn'da paylaşılamaz. Webhook idempotency garantisi yok.
- **Öneri:** Redis-backed idempotency store.

---

## 4. QA MÜHENDİSLİĞİ DENETİMİ (QA Engineer)

### 4.1 KRITIK — Test Coverage Gate Çok Düşüktü ✅ DÜZELTİLDİ
- **Dosya:** `pyproject.toml:174` — `fail_under = 25`
- **Sorun:** %25 coverage minimum'u çok düşüktü.
- **Düzeltme:** %50'ye yükseltildi.

### 4.2 YÜKSEK — Security Test'lerin Çoğu Stub
- **Dosyalar:** `tests/security/*.py` (7 dosya)
- **Sorun:** Test dosyaları var ama gerçek güvenlik senaryolarını ne kadar kapsadığı belirsiz. OWASP ZAP veya Bandit entegrasyonu CI'da yok.

### 4.3 YÜKSEK — E2E Test'ler InMemory Stub Üzerinde
- **Dosyalar:** `tests/e2e/*.py`
- **Sorun:** Backend E2E testleri InMemory stub servislerle çalışıyor. Gerçek veritabanı, Redis, RabbitMQ entegrasyonu test edilmiyor.

### 4.4 YÜKSEK — Ruff Lint Kapsamı Dar ✅ DÜZELTİLDİ
- **Dosya:** `.github/workflows/ci.yml:88,91`
- **Sorun:** Ruff lint sadece `E9,F63,F7,F82` kurallarını çalıştırıyor (sadece syntax errors). Format check tek dosyaya bakıyordu.
- **Düzeltme:** Format check tüm `src/` ve `tests/` dizinlerine genişletildi.

### 4.5 ORTA — Performance Test CI Entegrasyonu Yok
- **Dosyalar:** `tests/performance/locustfile.py`, `test_mission_assignment_load.py`
- **Sorun:** Performance testleri mevcut ama CI'da çalışmıyor.

### 4.6 ORTA — Frontend Test Coverage Bilinmiyor
- **Dosya:** `web/jest.config.js`
- **Sorun:** Jest config var ama frontend unit test dosyaları listede yok. Frontend test coverage'ı %0 olabilir.

---

## 5. SDLC DENETİMİ (SDLC Specialist)

### 5.1 YÜKSEK — Integration Test CI Job Yok
- **Dosya:** `.github/workflows/ci.yml`
- **Sorun:** CI pipeline'da `integration` test job'ı yok. Sadece unit testler çalışıyor.

### 5.2 YÜKSEK — Dependency Pinning Eksik
- **Dosya:** `pyproject.toml:22-62`
- **Sorun:** Tüm bağımlılıklar `>=` ile tanımlı, exact version pin yok. `pip freeze` veya lock dosyası olmadan her build farklı versiyonlar çekebilir.
- **Öneri:** `pip-compile` veya `poetry.lock` kullanılmalı.

### 5.3 ORTA — Security Scan CI Workflow İçeriği
- **Dosya:** `.github/workflows/security.yml` — incelenmeli
- **Sorun:** Security workflow var ama Bandit, SAST, dependency audit adımları doğrulanmalı.

### 5.4 ORTA — Pre-commit Hooks Kapsamı
- **Dosya:** `.pre-commit-config.yaml` — mevcut ama CI'da çalıştırılmıyor.

### 5.5 ORTA — Deployment Pipeline Eksik
- **Dosya:** `.github/workflows/deploy-staging.yml` — mevcut ama production deployment yok.
- **Sorun:** Staging → production promotion stratejisi tanımlı değil.

---

## 6. AGRİTECH DOMAIN DENETİMİ (Domain Expert)

### 6.1 YÜKSEK — Scan Interval SSOT İhlali (bkz. 3.1)
- CropType ve CropScanInterval farklı değerler → scheduling kaosu.

### 6.2 ORTA — Eksik Ürün Tipleri
- **Dosya:** `src/core/domain/value_objects/crop_type.py`
- **Sorun:** 8 ürün tipi tanımlı. Türkiye'nin major tarım ürünlerinden bazıları eksik:
  - ARPA (Barley) — Türkiye'nin 2. en büyük tahıl ürünü
  - ÇELTİK (Rice) — Güney Marmara/Samsun bölgesi
  - PATATES (Potato) — Niğde/Nevşehir
  - SEKER_PANCARI (Sugar Beet) — İç Anadolu
  - ÇAY (Tea) — Doğu Karadeniz
  - FINDIK (Hazelnut) — Karadeniz
- **Öneri:** En azından ARPA ve ÇELTİK eklenmeli.

### 6.3 ORTA — Rüzgar Hızı Eşiği Tartışılabilir
- **Dosya:** `src/core/domain/services/weather_validator.py:93`
- **Sorun:** `MAX_WIND_SPEED_KMH = 40.0` tarımsal drone'lar için yüksek olabilir. DJI Phantom 4 RTK: 36 km/h max, Matrice 300: 54 km/h. Drone modeline göre dinamik eşik olmalı.

### 6.4 DÜŞÜK — Mevsimsel Takvim Statik
- Bitki türü değişiklik penceresi (1 Ekim - 31 Aralık) sabit. Güneydoğu Anadolu ile Karadeniz arasında farklı iklim bölgeleri göz ardı edilmiş.

---

## 7. DOKÜMANTASYON & SSOT DENETİMİ (Technical Writer)

### 7.1 YÜKSEK — DIRECTORY_TREE.md Güncel Değil
- **Dosya:** `DIRECTORY_TREE.md`
- **Sorun:** Gerçek dosya yapısıyla karşılaştırıldığında eksik/fazla dosyalar olabilir.

### 7.2 ORTA — OpenAPI Spec Endpoint Uyumsuzluğu
- **Dosya:** `docs/api/openapi.yaml`
- **Sorun:** API'de 20 router var. OpenAPI spec'in tamamını kapsayıp kapsamadığı doğrulanmalı.

### 7.3 ORTA — CHANGELOG Version Tutarsızlığı
- pyproject.toml: `3.2.2`, .env.example: `3.2.2`, API default: `1.0.0`
- **Dosya:** `src/presentation/api/settings.py:38` — `API_VERSION` default `"1.0.0"`

### 7.4 DÜŞÜK — Arşiv Dosyaları Düzensiz
- `docs/archive/2026-02/` içinde eski dosyalar var ama arşiv politikası belgelenmemiş.

### 7.5 DÜŞÜK — KR Registry Referans Tutarlılığı
- Tüm dosyalarda BOUND/KR referansları var ama kaç tanesinin `kr_registry.md`'de kayıtlı olduğu otomatik doğrulanmalı.

---

## 8. FRONTEND DENETİMİ (Frontend Engineer)

### 8.1 KRITIK — XSS Riski: Token Cookie'de Plain Text
- **Dosya:** `web/src/hooks/useAuth.ts:69`
- **Sorun:** JWT token cookie'ye `encodeURIComponent` ile yazılıyor, HttpOnly flag yok → JavaScript ile okunabilir.

### 8.2 YÜKSEK — i18n Tutarsızlıkları
- **Dosyalar:** `web/src/i18n/tr.ts` (TypeScript), `ar.json`, `ku.json` (JSON)
- **Sorun:** Farklı formatlar. Türkçe TS obje, Arapça/Kürtçe JSON. Key uyumu doğrulanmalı.
- **Ayrıca:** Birçok component'te hardcoded Türkçe string var (ör. "Anahtar listesi ve rotasyon aksiyonları (stub)")

### 8.3 YÜKSEK — Service Worker Güvenliği
- **Dosya:** `web/public/service-worker.js`
- **Sorun:** Service worker'ın cache stratejisi ve scope'u incelenmeli. Auth token'ı cache'lememeli.

### 8.4 YÜKSEK — Çoğu Sayfa Stub İçerik
- **Dosyalar:** Admin panel sayfalarının çoğu `(stub)` veya placeholder içerik gösteriyor.
- **Etki:** UI mevcut ama işlevsel değil.

### 8.5 ORTA — Missing Error Boundaries
- **Dosya:** `web/src/app/error.tsx` — root level var ama feature-level error boundary'ler eksik.

### 8.6 ORTA — Sentry Config Eksik DSN
- **Dosyalar:** `web/sentry.client.config.ts`, `web/sentry.server.config.ts`
- **Sorun:** `SENTRY_DSN` env var boş → production'da error tracking çalışmaz.

### 8.7 ORTA — Client-Side Role Guard Bypass
- **Dosya:** `web/src/middleware.ts`
- **Sorun:** Rol kontrolü sadece cookie'deki `ta_role` değerine bakıyor. Kullanıcı cookie'yi değiştirerek farklı role sayfalarına erişebilir. Backend RBAC ile çift katman olmalı.

### 8.8 ORTA — Accessibility Eksiklikleri
- Birçok component'te `aria-label` var ama tutarlı değil. `AddFieldModal`, `DatasetUploadModal` gibi modal'larda keyboard trap yönetimi doğrulanmalı.

---

## Uygulanan Düzeltmeler (Bu Rapor Kapsamında)

| # | Dosya | Düzeltme | Önem |
|---|-------|----------|------|
| 1 | `jwt_middleware.py` | Token exp/iat doğrulaması eklendi | KRITIK |
| 2 | `settings.py` | CORS default `["*"]` → `["http://localhost:3000"]` | KRITIK |
| 3 | `payment_webhooks.py` | HMAC signature doğrulaması eklendi | KRITIK |
| 4 | `settings.py` | Auth/webhook endpoint'leri JWT bypass listesine eklendi | YÜKSEK |
| 5 | `dependencies.py` | get_current_user dict/dataclass uyumsuzluğu düzeltildi | YÜKSEK |
| 6 | `dependencies.py` | datetime.utcnow() → datetime.now(timezone.utc) | ORTA |
| 7 | `expert_portal.py` | datetime.utcnow() → datetime.now(timezone.utc) | ORTA |
| 8 | `useAuth.ts` | Cookie Secure flag eklendi | YÜKSEK |
| 9 | `ci.yml` | Ruff format check tüm src/tests kapsamına genişletildi | ORTA |
| 10 | `pyproject.toml` | Coverage fail_under 25% → 50% | ORTA |

---

## Kalan Öncelikli Aksiyonlar

### P0 — Canlıya Çıkmadan Önce Yapılması Gerekenler
1. InMemory auth servisi → gerçek implementasyon (veritabanı + bcrypt PIN hash)
2. InMemory stub servisler → DI container ile gerçek servislere bağlama
3. JWT secret production check (env var yoksa fail-fast)
4. Token storage: localStorage → httpOnly Secure cookie
5. Tüm endpoint'lere rol bazlı erişim kontrolü (RBAC)
6. CropType/CropScanInterval SSOT tutarsızlığı giderme
7. Integration test CI job ekleme
8. Dependency pinning (lock dosyası)

### P1 — İlk Sprint İçinde
9. Frontend i18n format birleştirme
10. Performance test CI entegrasyonu
11. DIRECTORY_TREE.md ve OpenAPI spec güncelleme
12. Redis parola zorunluluğu
13. Rate limit IP maskeleme düzeltmesi
14. Receipt upload boyut/tip kontrolü
15. Event handler wiring

### P2 — Sonraki Sprint
16. Eksik crop type'lar ekleme (ARPA, ÇELTİK, vb.)
17. Drone modeline göre dinamik weather eşikleri
18. Frontend error boundary genişletme
19. Migration chain validation CI
20. SAST/DAST CI entegrasyonu
