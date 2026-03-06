# TarlaAnaliz Platform — SSOT v1.2.0 Uyumluluk Denetim Raporu

**Tarih:** 2026-03-05
**SSOT Referansi:** `docs/TARLAANALIZ_SSOT_v1_2_0.txt` v1.2.0
**Denetim Kapsami:** 7 uzman perspektifinden derinlemesine analiz
**Durum:** UYUMSUZLUKLAR TESPiT EDiLDi

---

## Yonetici Ozeti

Platform, 7 farkli uzman perspektifinden (SDLC, SSOT Custodian, AgriTech Domain, Data Pipeline, Security, QA, Software Architect) derinlemesine denetlenmistir. Mimari temeller saglamdir (Clean Architecture + CQRS + Event-Driven), domain katmani SSOT kurallarina buyuk olcude uyumludur. Ancak **uygulama katmani** (runtime wiring, persistence, security) onemli bosluklar icermektedir.

| Kategori | Kritik | Yuksek | Orta | Dusuk |
|----------|--------|--------|------|-------|
| Guvenlik (Security Architect) | 4 | 6 | 6 | 3 |
| Mimari (Software Architect) | 3 | 2 | 3 | 3 |
| Veri Pipeline (Data Engineer) | 2 | 1 | 4 | 2 |
| Test/QA (QA Engineer) | 0 | 4 | 3 | 1 |
| SSOT Custodian | 0 | 1 | 1 | 0 |
| **TOPLAM** | **9** | **14** | **17** | **9** |

---

## BOLUM 1: SSOT CUSTODIAN / TECHNICAL WRITER BULGULARI

### DUZELTILDI: 92 Dosyada Eski BOUND Header (v1_1_0 → v1_2_0)

`src/` dizinindeki 92 kaynak dosya eski `BOUND: TARLAANALIZ_SSOT_v1_1_0.txt` referansi tasiyordu.
Bu denetim kapsaminda tum dosyalar `v1_2_0` olarak guncellendi.

**Etkilenen katmanlar:**
- `src/core/domain/entities/` (4 dosya: field, mission, pilot, user)
- `src/core/domain/services/` (7 dosya)
- `src/core/domain/value_objects/` (6 dosya)
- `src/core/ports/` (3 dosya)
- `src/application/commands/` (12 dosya)
- `src/application/queries/` (13 dosya)
- `src/application/services/` (14 dosya)
- `src/infrastructure/security/` (4 dosya)
- `src/presentation/api/middleware/` (7 dosya)
- `src/presentation/api/v1/endpoints/` (22 dosya)

### SSOT-01 (Orta): 21 Test Dosyasinda Eski Docstring Referansi

21 test dosyasinda docstring govdesinde "SSOT v1.0.0" ifadesi kalmistir.
BOUND header'lar dogru (`v1_2_0`), ancak docstring govdeleri tutarsiz.

---

## BOLUM 2: GUVENLIK MiMARi (SECURITY ARCHITECT) BULGULARI

### KRiTiK BULGULAR

| ID | KR | Bulgu | Dosya |
|----|-----|-------|-------|
| CRIT-01 | KR-050 | Hardcoded demo credentials (`+905555555555` / `1234`) auth endpoint'inde | `src/presentation/api/v1/endpoints/auth.py:53-67` |
| CRIT-02 | KR-050 | JWT secret varsayilan deger (`dev-only-secret`) ile calisiyor | `src/presentation/api/settings.py:57` |
| CRIT-03 | KR-066 | CORS varsayilan `*` (wildcard); env var isim uyumsuzlugu | `src/presentation/api/settings.py:47` |
| CRIT-04 | - | Docker Compose'da servis sifreleri acik metin (postgres, rabbitmq, minio) | `docker-compose.yml:15,50,71` |

### YUKSEK BULGULAR

| ID | KR | Bulgu |
|----|-----|-------|
| HIGH-01 | KR-050 | Brute-force lockout implementasyonu yok (16 deneme/30dk kilitleme) |
| HIGH-02 | KR-050 | JWT middleware token suresi (exp) kontrol etmiyor — tokenler sonsuza kadar gecerli |
| HIGH-03 | KR-066 | Auth cookie'lerde `Secure` ve `HttpOnly` flag'leri yok |
| HIGH-04 | KR-033 | Webhook imza dogrulamasi no-op — herhangi bir string kabul ediliyor |
| HIGH-05 | KR-063 | Frontend/backend rol enum uyumsuzlugu (13 vs 11 rol) |
| HIGH-06 | KR-063 | Admin odeme endpoint'leri yanlis rol adi kullaniyor (`"admin"` vs `"CENTRAL_ADMIN"`) |

### ORTA BULGULAR

| ID | Bulgu |
|----|-------|
| MED-01 | PII filter ve grid anonymizer `request.state.roles` yerine `user.roles` okuyor (her zaman bos) |
| MED-02 | RabbitMQ varsayilan `guest/guest` credentials |
| MED-03 | Auth token `localStorage`'da saklanıyor (XSS riski) |
| MED-04 | PIN artifact browser storage'da tutuluyor |
| MED-05 | Swagger/ReDoc/OpenAPI tum ortamlarda acik |
| MED-06 | Request body boyut limiti yok |

---

## BOLUM 3: VERi PiPELINE (DATA ENGINEER) BULGULARI

### KRiTiK BULGULAR

| ID | KR | Bulgu |
|----|-----|-------|
| DS-1 | KR-072 | `datasets` tablosu icin Alembic migration yok — 9+1 state machine veritabaninda persist edilemiyor |
| SCH-1 | KR-081 | `schemas/` dizininde JSON Schema dosyalari yok — contract-first validation calismiyor |

### YUKSEK BULGULAR

| ID | KR | Bulgu |
|----|-----|-------|
| MIG-2 | KR-018 | `available_bands` ve `band_class` kolonlari `analysis_jobs` migration'inda yok |

### ORTA BULGULAR

| ID | Bulgu |
|----|-------|
| SCH-2 | `ContractValidator` sinifi bulunamiyor — SchemaRegistry var ama validation yok |
| ANAL-1 | `band_class` AnalysisJob'da bare string, BandClass enum'a baglanmamis |
| ANAL-2 | `start_processing()` band_class set edilmis mi kontrol etmiyor |
| MAN-1 | `available_bands` dataset intake zamaninda dogrulanmiyor, sadece CALIBRATED gecisinde |

### POZiTiF BULGULAR

- Dataset lifecycle 9+1 state machine domain katmaninda tam ve dogru uygulanmis (KR-072)
- drone_capability_matrix.yaml eksiksiz ve SSOT uyumlu (KR-018/082/084)
- Graceful degradation (BASIC_4BAND/EXTENDED_5BAND/THERMAL) dogru implemente (KR-018/082)
- Termal pipeline value object'leri dogru (KR-084: CWSI, canopy_temp, delta_t)
- RabbitMQ event-driven architecture iyi tasarlanmis (idempotency, DLQ, retry)

---

## BOLUM 4: MiMARi (SOFTWARE ARCHITECT) BULGULARI

### KRiTiK BULGULAR

| ID | Bulgu |
|----|-------|
| V-REPO-1 | 16/18 repository implementasyonu bos stub (3 satirlik TODO) |
| V-DI-1 | DI container / composition root yok — servisler hic wire edilmiyor |
| V-DI-2 | 17 API endpoint'i hardcoded InMemory stub kullaniyor |

### YUKSEK BULGULAR

| ID | Bulgu |
|----|-------|
| V-STATUS-1 | MissionStatus 3 farkli yerde 3 farkli sekilde tanimli (entity, VO, schema) |
| V-EVT-1 | Event dispatcher typed event verisini kaybediyor — handler'lar bos DomainEvent aliyor |

### ORTA BULGULAR

| ID | Bulgu |
|----|-------|
| V-CQRS-1 | Commands sync, Queries async — repository port'lari async ama commands sync cagriliyor |
| V-DTO-1 | Field entity, DTO ve API schema 3 farkli shape'e sahip |
| V-DTO-2 | Application katmani core port'lari farkli signature ile yeniden tanimliyor |

### POZiTiF BULGULAR

- Katman ayriligi dogru: domain katmaninda infrastructure import'u yok
- Hexagonal architecture yapisal olarak dogru (18 port, 7 external adapter)
- Dongusel bagimlilik (circular dependency) tespit edilmedi
- Domain entity'ler invariant'lari `__post_init__` ile zorluyor
- Value object'ler frozen/immutable
- Frontend Next.js App Router + rol bazli route gruplari iyi yapilandirilmis

---

## BOLUM 5: TEST / QA (QA ENGINEER) BULGULARI

### YUKSEK BULGULAR

| ID | KR | Bulgu |
|----|-----|-------|
| GAP-01 | KR-041 | `tools/breaking_change_detector.py` mevcut degil |
| GAP-02 | KR-081 | `test_examples_match_schemas.py` mevcut degil |
| GAP-03 | KR-081 | `schemas/` dizini bos — contract-first test'ler calismiyor |
| GAP-06 | KR-041 | 24+ KR icin kabul testi yok (KR-014, 016, 020-026, 029, 031, 032, 064, 065, 070, 073, 084 vb.) |

### ORTA BULGULAR

| ID | Bulgu |
|----|-------|
| GAP-04 | Backend coverage threshold %25 — KR-041 hedefi %80+ |
| GAP-07 | Frontend'de sifir Jest unit test dosyasi |
| GAP-10 | CI pipeline'da integration/security testleri calistirilmiyor |

### POZiTiF BULGULAR

- 60 test dosyasi mevcut (22 unit, 7 integration, 4 e2e, 7 security, 2 performance, 7 presentation)
- BOUND header disiplini mukemmel — tum 60 test dosyasinda dogru `v1_2_0` header
- KR-018 (kalibrasyon hard gate) unit, integration ve E2E katmanlarinda iyi test edilmis
- KR-033 (odeme + manuel onay) birden fazla test dosyasinda kapsamli
- SSOT compliance gate (`scripts/check_ssot_compliance.py`) CI'a entegre
- Guvenlik test suite guçlu (7 dosya: PII, rate limit, mTLS, RBAC, brute force, webhook, grid)

---

## BOLUM 6: AgriTech DOMAIN EXPERT BULGULARI

### POZiTiF BULGULAR

- `config/drone_registry.yaml`: 5 drone/sensor kombinasyonu SSOT KR-001/KR-030/KR-034 ile tam uyumlu
- `config/drone_capability_matrix.yaml`: Band siniflari, NDRE duzeltme ofsetleri, termal sensor bilgisi eksiksiz
- Graceful degradation kurallari (TEMEL/GENISLETILMIS/KAPSAMLI) SSOT KR-018/082/084 ile birebir eslesme
- Bitki turu bazli kapasite profilleri (CropOpsProfile) KR-015 ile uyumlu
- Radyometri notu (goreli vs mutlak kalibrasyon) tum ilgili dosyalarda dogru referanslanmis
- DJI tedarik bagimsizligi plani (KR-034) "aktif operasyon plani" olarak guncel

---

## BOLUM 7: SDLC SUREC DENETiMi

### BULGULAR

| ID | KR | Bulgu | Durum |
|----|-----|-------|-------|
| SDLC-01 | KR-041 | PR Gate checklist sablonu mevcut | PASS |
| SDLC-02 | KR-041 | Secret scan (detect-secrets) pre-commit hook'ta aktif | PASS |
| SDLC-03 | KR-041 | Breaking change detector (`tools/breaking_change_detector.py`) yok | FAIL |
| SDLC-04 | KR-041 | CI'da integration/e2e testleri calistirilmiyor | FAIL |
| SDLC-05 | KR-041 | pip-audit ve Lighthouse hatalari yutuluyor (`|| echo`) | FAIL |
| SDLC-06 | KR-041 | Deploy pipeline sahte (echo komutlari) | FAIL |
| SDLC-07 | KR-041 | Migration chain validation sadece dosya listeler, `alembic upgrade` calistirmaz | FAIL |
| SDLC-08 | KR-041 | Frontend unit test yok (`console.log` stub) | FAIL |
| SDLC-09 | Governance | CHANGELOG.md mevcut, SemVer uygulanıyor | PASS |
| SDLC-10 | Governance | CONTRACTS_VERSION.md v1.1.0 aktif, checksum dosyasi var | PASS |

---

## BU DENETiMDE YAPILAN DUZELTiLER

| # | Duzeltme | Etki |
|---|----------|------|
| 1 | 92 dosyada BOUND header `v1_1_0` → `v1_2_0` guncellendi | SSOT drift giderildi |

---

## ONERiLEN ONCELIKLI AKSiYON PLANI

### Faz 0 — Acil Guvenlik (BLOCKER)
1. Hardcoded auth stub'i kaldir, gercek PIN + bcrypt/argon2 servisi bagla
2. JWT middleware'e `exp` kontrolu ekle (mevcut `JWTHandler` kullan)
3. JWT secret icin production startup guard ekle
4. CORS wildcard'i kaldir, env var ismini duzelt
5. Docker Compose sifrelerini `.env` dosyasina tasi
6. Webhook imza dogrulamasini HMAC-SHA256 ile implemente et
7. Admin endpoint rol isimlerini `CENTRAL_ADMIN` olarak duzelt

### Faz 1 — Mimari Tamamlama
8. 16 bos repository implementasyonunu tamamla
9. DI composition root / container olustur
10. InMemory stub'lari endpoint'lerden kaldir
11. MissionStatus tanimlarini tek kaynaga indir (3 farkli tanim → 1)
12. Event dispatcher'da typed event reconstruction'i duzelt

### Faz 2 — Veri Pipeline & Contract-First
13. `datasets` tablosu icin Alembic migration olustur
14. `available_bands` ve `band_class` kolonlarini `analysis_jobs`'a ekle
15. `schemas/` dizinine KR-081.1 AnalysisJob ve KR-081.2 AnalysisResult JSON Schema'larini ekle
16. `tools/breaking_change_detector.py` olustur
17. `test_examples_match_schemas.py` olustur

### Faz 3 — Test & CI/CD
18. CI pipeline'da integration + security testlerini aktif et
19. Backend coverage threshold'u %25'ten %60+'a yukselt
20. Frontend Jest unit testleri yaz
21. pip-audit ve Lighthouse'dan hata yutmayi kaldir
22. Eksik KR kabul testlerini yaz (en az KR-070, 072, 073, 084)

---

## SONUC

Platform mimarisi ve domain modeli guclu bir temel uzerine insa edilmistir. SSOT governance
sistemi (BOUND header'lar, KR referanslari, contract versioning) disiplinli uygulanmaktadir.
Ancak runtime implementasyonu (repository'ler, DI wiring, guvenlik katmani) henuz uretim
seviyesinde degildir. Faz 0'daki guvenlik duzeltmeleri canli ortama cikmadan once **zorunludur**.
