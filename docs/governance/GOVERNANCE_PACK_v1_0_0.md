BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

# TarlaAnaliz Governance Pack v1.0.0 (2026-02-15)

Bu doküman **“tek gerçek kaynak (SSOT)” + “contract-first”** mimarisinde, kodlama başlamadan önce **SDLC (Software Development Life Cycle)** disiplinini kilitlemek için hazırlanmıştır.  
Hedef: **drift (sapma) ≈ 0**, **breaking change (kırıcı değişiklik) = kontrollü**, **incident (olay) çözüm süresi = hızlı ve kanıtlı**.

---

## 0) Rol ve Sorumluluklar (RACI)

**Proje Sahibi (Sen):** ürün liderliği, saha operasyonu, uzman ağı, satış/ortaklık, finansal sürdürülebilirlik.  
**Paşa (Sistem Mimarı + Güvenlik + SDLC):** mimari/SDLC sertliği, güvenlik/threat model, observability, incident response tasarımı.  
**Ziraat/Bitki Koruma Uzmanı:** ground truth (saha doğrulaması), etiketleme standardı, alarm eşiği doğrulaması, etik sorumluluk.  
**Saha Operasyon Sorumlusu:** istasyon SOP, pilot performansı, veri kalitesi, teslimat SLA.

**RACI kuralı:**  
- SSOT / KR / Contracts değişiklikleri → **Paşa Accountable**, Proje Sahibi **Approver** (gerekirse).  
- Saha SOP / veri kalite standardı → Proje Sahibi **Accountable**, uzman + saha ops **Consulted**.

---

## 1) Tek Gerçek Kaynak (SSOT) Disiplini

### 1.1 Altın kural
- **SSOT** = “Normatif gerçek” (MUST kuralları, kabul testleri, cross-ref).
- **Contracts** = “Makine-doğrulanabilir gerçek” (schema, enum, example).
- **Repo/Servis kodu** = Uygulama; **SSOT + Contracts’a uyar**.

### 1.2 Drift’i sıfıra indirme ilkeleri
- Aynı kural **iki ayrı yerde** “detaylı” anlatılmaz.  
  - Detay: SSOT + Contracts  
  - Akış anlatımı: DOCX (özet + referans)
- Her KR, **tek şablon**la yazılır (Amaç → MUST → Kanıt → Audit → Hata → Test → Cross-refs).
- “Domain paketleri indeksi” sadece navigasyondur; normatif metin KR’nin içindedir.

---

## 2) Değişiklik Kontrolü (Change Control)

### 2.1 Değişiklik sınıfları
1) **Doc-only** (dokümantasyon): davranış değiştirmez.  
2) **Non-breaking** (kırmayan): yeni alan ekler ama geriye uyumludur.  
3) **Breaking** (kırıcı): alan kaldırma/yeniden adlandırma, enum daraltma, zorunlu alan ekleme, semantik değişim.

### 2.2 Versiyon politikası (SemVer)
- **MAJOR**: breaking change  
- **MINOR**: non-breaking feature  
- **PATCH**: doc/bugfix

### 2.3 PR Gate (Pull Request Gate) — zorunlu kontrol listesi
Her PR için minimum:
- [ ] SSOT/KR değiştiyse: ilgili KR’de **Test/Kabul** güncellendi
- [ ] Contracts değiştiyse: schema + example + test güncellendi
- [ ] Breaking-change detector çalıştı (tools/breaking_change_detector.py)
- [ ] Version bump yapıldı (CONTRACTS_VERSION.md / CHANGELOG.md)
- [ ] Migrasyon notu yazıldı (docs/migration_guides)

### 2.4 “Breaking change” süreci (hard gate)
- 1) PR içinde **Breaking Change Justification** (gerekçe) şart
- 2) Migrasyon rehberi şart
- 3) Eski sürüm için **deprecation window (kademeli kaldırma)** planı
- 4) CI: `test_no_breaking_changes.py` geçmeden merge yok

---

## 3) Contracts-First Gate (CI/CD)

### 3.1 Contracts repo zorunlulukları
- `schemas/` + `enums/` + `docs/examples/` birlikte yürür.
- Her yeni schema için:
  - [ ] JSON Schema dosyası
  - [ ] en az 1 example.json
  - [ ] `test_examples_match_schemas.py` ile doğrulama

### 3.2 Uygulama repo zorunlulukları
- Platform / EdgeKiosk / Worker:
  - Contracts versiyonu pin’li olmalı (dependency pinning).
  - CI’de: “contracts version mismatch” durumunda fail.

---

## 4) Güvenlik Modeli (Threat Model) — Kısa Kanonik

Saldırı yüzeyi hattı: **Edge → Ingress → Storage → Worker → Platform**.

### 4.1 En kritik güvenlik kabulleri
- Ham dosya = **untrusted input (güvenilmez girdi)**.
- Worker = **inbound kapalı** (KR-070).
- One-way data flow = **ağ politikası** ile kanıtlı (KR-071).
- Dataset lifecycle + chain-of-custody = **kontrat** (KR-072).
- AV1/AV2 + verification = **kanıt üretir** (KR-073).

### 4.2 Minimum güvenlik kontrolleri (MUST)
- mTLS (mutual TLS) cihaz kimliği (EdgeKiosk) + iptal/rotasyon
- WAF / API Gateway rate limit (oran sınırlama) + authn/authz (kimlik/izin)
- Secrets (gizli anahtarlar) sadece vault/secret store; repo’ya yazılmaz
- SBOM (Software Bill of Materials) + imza doğrulama (signature verification)
- Dependency pinning + güvenlik taraması (SCA)

---

## 5) Gözlemlenebilirlik (Observability) — Minimum Paket

### 5.1 Her servis için zorunlu sinyaller
- **Logs (kayıtlar):** structured JSON, `correlation_id`, `dataset_id`, `job_id`, `actor_id`
- **Metrics (metrikler):**
  - ingest throughput, queue depth, job latency, error rates
  - AV pass/fail count, hash mismatch count
- **Tracing (iz sürme):** ingest → verify → calibrate → dispatch → analyze → publish zinciri

### 5.2 Olay isimleri (önerilen)
- `SECURITY.DENY` (mTLS_fail/allowlist_fail/signature_fail)
- `INGEST.RAW_RECEIVED`
- `MANIFEST.SEALED`
- `AV1.PASS/FAIL`, `AV2.PASS/FAIL`
- `HASH.VERIFIED`, `HASH.MISMATCH`
- `CALIBRATION.PASS/FAIL`, `QC.PASS/WARN/FAIL`
- `JOB.DISPATCHED`, `JOB.REJECTED`, `JOB.COMPLETED`
- `RESULT.PUBLISHED`

---

## 6) Dayanıklılık (Reliability) — Offline/Low-Bandwidth Gerçeği

### 6.1 Transfer prensipleri
- Chunk upload (parçalı yükleme) + resume (devam ettirme)
- Idempotency (yinelenebilirlik): aynı transfer tekrar gelirse “ikinci kez yazma” değil “aynı sonucu üret”
- Retry/backoff (yeniden deneme): kontrollü ve sınırlı

### 6.2 Kuyruk dayanıklılığı
- Dispatch/Queue: at-least-once (en az bir kez teslim) varsayımı
- Consumer (Worker): idempotent job handling (job_id bazlı)

---

## 7) Incident Response (Olay Müdahalesi) — 30 Dakika Kuralı

**Hedef:** “Ne oldu?” sorusunu **30 dakika içinde** kanıtlı cevaplamak.

### 7.1 SEV sınıfları
- **SEV-1:** veri sızıntısı şüphesi, worker izolasyonu ihlali, kanıt zinciri kırıldı
- **SEV-2:** analiz pipeline durdu, kuyruk tıkandı, kalibrasyon gate çöktü
- **SEV-3:** performans düşüşü, tekil istasyon sorunu

### 7.2 İlk 15 dakikada yapılacaklar (runbook)
1) Etkiyi sınırla: ilgili istasyonu / token’ı / sertifikayı iptal et (revocation)
2) Kanıtı koru: WORM audit log snapshot al
3) Trace et: correlation_id üzerinden zinciri çıkar
4) Karar ver: quarantine / reject / rollback

### 7.3 Post-incident (72 saat)
- Root cause analysis (kök neden analizi)
- KR/Contracts güncellemesi gerekiyorsa change-control ile geç
- Test ekle: aynı olay tekrar edemesin

---

## 8) “Mükemmellik” için Pratik Kapılar (Günlük iş akışı)

### 8.1 Günlük disiplin (her gün)
- SSOT/Contracts drift kontrolü
- Açık PR’larda gate checklist
- Observability dashboard kontrolü (ingest + queue + latency)

### 8.2 Haftalık disiplin (her hafta)
- Threat model gözden geçirme (yeni endpoint/akış var mı?)
- SBOM + dependency audit
- Saha SOP geri bildirimleriyle “kural netleştirme”

---

## 9) Cross-refs (Kanonik KR’ler)
- **KR-017:** şemsiye analiz hattı
- **KR-018 / KR-082:** kalibrasyon hard gate + spektral kapasite algılama
- **KR-034:** drone tedarik bağımsızlığı
- **KR-050:** kimlik doğrulama (phone + PIN)
- **KR-063:** roller ve yetkiler (RBAC)
- **KR-066:** güvenlik ve KVKK (PII ayrımı)
- **KR-070:** worker isolation
- **KR-071:** one-way data flow + allowlist yerleşimi
- **KR-072:** dataset lifecycle + chain-of-custody (contract-first)
- **KR-073:** untrusted input + AV1/AV2 + sandbox
- **KR-081:** contract-first / schema gates
- **KR-084:** termal veri işleme ve sulama stresi

---

## 10) Ek: PR Şablonu (kopyala-yapıştır)

**Değişiklik türü:** doc-only / non-breaking / breaking  
**Etkilenen KR’ler:** KR-xxx, KR-yyy  
**Etkilenen Contracts:** schema/enums/examples  
**Risk:** düşük/orta/yüksek  
**Kabul testleri:** (E2E senaryoları listesi)  
**Migrasyon notu:** (varsa)  
