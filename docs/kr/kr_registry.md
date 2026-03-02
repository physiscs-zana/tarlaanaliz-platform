# TarlaAnaliz SSOT — KR Registry (Kanonik)


## KR Domain Paketleri İndeksi (Navigasyon)

**KR Şablonu (Kanonik):**
1) Amaç
2) Kapsam / Applies-to
3) Zorunluluklar (MUST) — test edilebilir maddeler
4) Kanıt / Artefact (manifest, raporlar, sertifika, event)
5) Audit / Log (olay adları + correlation_id)
6) Hata Modları / Quarantine kararları
7) Test / Kabul Kriterleri (E2E senaryolar)
8) Cross-refs (ilgili KR’ler)

**Not:** Bu bölüm sadece navigasyon içindir. Asıl normatif metin her KR başlığının altındadır.

### A) Security & Isolation
- KR-070 — Worker Isolation & Egress Policy
- KR-071 — One-way Data Flow + Allowlist Yerleşimi (Ingress)
- KR-073 — Untrusted File Handling + AV1/AV2 + Sandbox

### B) Data Lifecycle & Evidence (Chain of Custody)
- KR-072 — Dataset Lifecycle + Kanıt Zinciri (manifest/hash/signature/verification)
- KR-018 — Radiometric Calibration Hard Gate (QC + Certificate)
- KR-081 — Contract-First / Schema Gates (CI)

### C) Orchestration & Operations
- KR-017 — YZ Analiz Hattı (Şemsiye KR: 070–073 ayrıştırması)
- KR-015 — Pilot kapasite/planlama alt kuralları

### D) Payments & Governance
- KR-033 — Ödeme + Manuel Onay + Audit


**Tarih:** 2026-02-02  
**Amaç:** KR kodlarını tekil, izlenebilir ve bileşenler arası tutarlı tutmak.

## Temel kurallar (cross-ref standardı)

1) **Kanonik kimlik:** Her iş kuralı tek bir **[KR-xxx]** kimliğine sahiptir.  
2) **Alias (uyumluluk etiketi):** Tarihsel/harici dokümanlar başka bir KR kodu kullanıyorsa, bu kod **alias** olarak tutulur ve **kanonik KR**’ye bağlanır. Alias **yeni normatif metin üretmez**.  
3) **Component SSOT’lar (filtered view):**  
   - `contracts_ssot.md`, `platform_ssot.md`, `edgekiosk_ssot.md`, `worker_ssot.md` dosyaları KR üretmez.  
   - Sadece bu registry’den **kendine düşen KR’leri** listeler ve *bileşen özel uygulama notu* ekler.  
4) **Referans biçimi:** Metinde her zaman `[KR-018]` gibi yazılır.  
   - Eğer alias kullanılıyorsa: `[KR-082] (alias of KR-018)` şeklinde belirtilir.  
5) **Değişiklik kuralı:** Bir KR’nin anlamı değişecekse aynı kodu “kaydırma” yapma.  
   - Ya KR’nin sürüm notunu yaz,  
   - Ya yeni KR aç, eskisini “deprecated” et.

## KR haritası (kanonik tablo)

| KR | Başlık | Applies To | Kaynaklarda Geçiş | Kısa normatif özet |
| --- | --- | --- | --- | --- |
| [KR-000](#kr-000) | Bu doküman seti nasıl okunur? | contracts, edge-kiosk, platform, worker | SSOT, KANONIK, DEV | Saha adımları ve DJI entegrasyon ayrıntıları ayrı bir SOP dokümanında tutulur |
| [KR-001](#kr-001) | Proje Özeti | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | *Amaç:** Çiftçilerin ürün kaybını erken uyarı ile azaltmak ve dönüm bazlı analiz hizmeti satmak. Başlangıç bölgesi GAP, ardından Türkiye geneline ölçekleme. |
| [KR-002](#kr-002) | Harita Katmanı Anlamları (Renk + Desen) | contracts, edge-kiosk, platform, worker | SSOT, KANONIK, DEV | \| Katman \| Renk \| Desen \| |
| [KR-010](#kr-010) | Web (PWA) - Genel | platform | SSOT, KANONIK |  |
| [KR-011](#kr-011) | Kullanıcı Rolleri ve Temel Yaklaşım | edge-kiosk, worker | SSOT, KANONIK | \| Rol \| Sorumluluk \| |
| [KR-012](#kr-012) | İş Planlaması | platform | SSOT, KANONIK |  |
| [KR-013](#kr-013) | Çiftçi Üyeliği ve Tarla Yönetimi | platform, worker | SSOT, KANONIK | *Üyelik:** PWA veya web üzerinden üye olunur. İl, ilçe, ad, soyad ve telefon numarası alınır; üye olunca kendi sayfasına yönlendirilir. |
| [KR-014](#kr-014) | Kooperatif/Üretici Birliği Üyeliği ve İşleyiş | platform, worker | SSOT, KANONIK | *Doğrulama:** Hesap 'Onay Bekliyor' açılır. Evrak kontrolü sonrası Merkez yönetim 'Aktif' yapar; eksik evrak varsa aktif edilemez. |
| [KR-015](#kr-015) | Drone Pilotları (DJI Mavic 3M ile Uçuş) | edge-kiosk, platform, worker | SSOT, KANONIK | *Üyelik/Kayıt:** İl, ilçe, ad soyad, telefon; drone modeli ve seri numarası; hizmet verdiği mahalle/köy listesi (başlangıçta opsiyonel). Drone seri numarası doğrulama referansıdır. |
| [KR-016](#kr-016) | Drone - Tarla - Bitki Eşleştirme Politikası (Routing) | worker | SSOT, KANONIK | *Amaç:** Veri setini doğru FieldID ve o tarihte geçerli bitki türü ile eşleştirip doğru bitki-özel YZ modelini otomatik seçmek. |
| [KR-017](#kr-017) | YZ Modeli ile Analiz | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | *Veri Akışı:** "FieldID + bitki türü + MissionID; PII yok" bu bilgiler sadece uçuş yapacak drone pilotuna ve hafıza kartlarına işlenir. |
| [KR-018](#kr-018) | Tam Radyometrik Kalibrasyon Zorunluluğu (Radiometric Calibration: ışık/sensör etkilerini düzeltme) | contracts, edge-kiosk, platform, worker | SSOT, KANONIK, DEV | Model eğitimi (training: modelin öğrenmesi) ve saha sonuçları arasında tutarlılık (training-serving parity: eğitim/çalıştırma aynı dağılım). |
| [KR-019](#kr-019) | Expert Portal (Uzman İnceleme) | platform, worker | SSOT, KANONIK, DEV | Uzman portalı, modelin düşük güven verdiği veya çelişkili durumlarda manuel inceleme için kullanılır (**PII görünmez**) |
| [KR-020](#kr-020) | Ücretlendirme | platform | SSOT, KANONIK |  |
| [KR-021](#kr-021) | Genel Prensip | platform, worker | SSOT, KANONIK | Ücretler bitki türü ve analiz seçeneğine göre: tek seferlik analiz veya yıllık abonelik |
| [KR-022](#kr-022) | Fiyat Yönetimi Politikası | platform | SSOT, KANONIK | Fiyatlar uygulamada serbest **yazılmaz**; tek kaynak **PriceBook** (Fiyat Kataloğu) |
| [KR-023](#kr-023) | Örnek Fiyat Kurgusu (Pamuk) | platform, worker | SSOT, KANONIK | \| Seçenek \| Liste Fiyat \| İlk Yıl / Abonelik Kurgusu \| |
| [KR-024](#kr-024) | Önerilen Tarama Periyodu (Gün) | platform | SSOT, KANONIK | \| Bitki \| Önerilen Periyot (gün) \| |
| [KR-025](#kr-025) | Analiz İçeriği (Hizmet Kapsamı) | worker | SSOT, KANONIK | *Temel İlke:** Sistem ilaçlama kararı **vermez**; yalnızca tespit, risk skoru ve erken uyarı sağlar. |
| [KR-026](#kr-026) | Sunum Biçimi | platform | SSOT, KANONIK | Harita katmanları (ısı haritası / grid / zonlama) |
| [KR-027](#kr-027) | Abonelik Planlayıcı (Subscription Scheduler) | platform, worker | SSOT, DEV | *Amaç:** Yıllık abonelik seçen kullanıcılar için otomatik, periyodik Mission üretimi. |
| [KR-028](#kr-028) | Mission Yaşam Döngüsü ve SLA Alanları | platform, worker | SSOT, DEV | *Mission Tanımı:** Bir tarlanın belirli bir tarihte yapılacak tek analiz görevi. Tek seferlik talepten veya yıllık abonelikten oluşabilir. |
| [KR-029](#kr-029) | YZ Eğitim Geri Bildirimi (Training Feedback Loop) | contracts, platform, worker | SSOT, DEV | *Amaç:** Uzman düzeltmelerini YZ modeline geri beslemek ve model iyileştirmesi yapmak. |
| [KR-030](#kr-030) | Notlar, Sınırlar ve Uyum | edge-kiosk, worker | SSOT, KANONIK, DEV | **Drone standardı:** Başlangıçta DJI Mavic 3M dışında veri kabul edilmez (sonraki fazda değerlendirilir) |
| [KR-031](#kr-031) | Pilot Hakediş ve Ödeme Politikası | platform | SSOT, KANONIK | Pilotlar, bir ay içinde **ONAYLANMIŞ** görevlerde taradıkları alan üzerinden hakediş kazanır |
| [KR-032](#kr-032) | Training Export Standardı | contracts, platform, worker | SSOT, KANONIK, DEV | *Amaç:** Uzman feedback'lerini standart formatta export ederek model eğitim pipeline'ına aktarmak. |
| [KR-033](#kr-033) | Ödeme ve Manuel Onay (Müşteri Tahsilat Akışı) | platform, worker | SSOT, KANONIK | *Amaç:** Çiftçi / Kooperatif / Üretici Birliği tarafından açılan **tek seferlik Mission** veya **yıllık Subscription** taleplerinde tahsilatı standartlaştırmak ve talebin “işlenebilir” hale gelmesini … |
| [KR-040](#kr-040) | Güvenlik Kabul Kriterleri/Test Checklist (SDLC Entegrasyonu) | platform | SSOT, KANONIK | *Amaç:** TXT repo mantalitesindeki savunma-derinliği (defense-in-depth) güvenlik yaklaşımını, ölçülebilir kabul kriterlerine ve SDLC kapılarına (PR/CI/Release/Ops) bağlamak. |
| [KR-041](#kr-041) | SDLC Kapıları (Gate) - Zorunlu Kontroller | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | Contracts pinleme: CONTRACTS_VERSION (SemVer) + CONTRACTS_SHA256 zorunlu; değişiklikte breaking-change kontrolü |
| [KR-042](#kr-042) | Kabul Kriterleri Matrisi | edge-kiosk, platform, worker | SSOT, KANONIK | \| Güvenlik Katmanı \| Kabul Kriteri (DoD) \| Test Kanıtı \| SDLC Gate \| |
| [KR-043](#kr-043) | Test Checklist (Senaryo Bazlı) | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | \| Senaryo \| Adımlar (özet) \| Beklenen Sonuç \| Kanıt/Artefakt \| |
| [KR-050](#kr-050) | Kimlik Doğrulama ve Üyelik Akışı (Sade Model) | worker | SSOT, KANONIK | Kimlik bilgisi olarak yalnızca **Telefon Numarası** kullanılır (E-posta ve TCKN **toplanmaz**) |
| [KR-060](#kr-060) | Ürün/Teknik Spesifikasyondan Normatif | platform | SSOT, KANONIK |  |
| [KR-061](#kr-061) | Amaç ve Sabit Çerçeve | platform, worker | SSOT, KANONIK | Drone: DJI Mavic 3M |
| [KR-062](#kr-062) | Tasarım İlkeleri | edge-kiosk, platform, worker | SSOT, KANONIK | 1. **Tek kaynak gerçek:** API ve veri modeli. Web (PWA) iş kuralı kopyalamaz. |
| [KR-063](#kr-063) | Roller ve Yetkiler (RBAC) | edge-kiosk, platform, worker | SSOT, KANONIK | \| Rol Kodu \| Kısa Tanım \| Özet Yetki \| |
| [KR-064](#kr-064) | Harita Katman Standardı (Layer Registry) | platform | SSOT, KANONIK, DEV | Katmanlar web (PWA) arayüzünde aynı Layer Registry üzerinden tanımlanır. Renk + desen/ikon + opaklık + öncelik tutarlı olmalıdır. |
| [KR-065](#kr-065) | Pilot Hakediş Doğrulama (Expected vs Observed) | platform | SSOT, KANONIK | **Expected Area:** FieldBoundary veya Mission flightplan sınırı (m²) |
| [KR-066](#kr-066) | Güvenlik ve KVKK | edge-kiosk, platform | SSOT, KANONIK | PII ayrı veri alanında tutulur; raporlama ve KPI katmanı pseudonymous kimliklerle çalışır |
| [KR-070](#kr-070) | YZ Analiz İzolasyonu (Worker Isolation) | worker | SSOT, KANONIK | Inbound kapalı; egress allowlist; job pull; calibrated+evidence hard gate |
| [KR-071](#kr-071) | Tek Yönlü Veri Akışı + Allowlist Yerleşimi | edge-kiosk, platform, worker | SSOT, KANONIK | Allowlist Ingress’te; mTLS ana kontrol; akış Edge→Platform→Storage/Queue→Worker→Platform→Web |
| [KR-072](#kr-072) | Dataset Lifecycle + Kanıt Zinciri (Contract-First) | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | Dataset state machine + manifest/hash/signature + AV1/AV2 + verification |
| [KR-073](#kr-073) | Untrusted File Handling + Malware (AV1/AV2) | edge-kiosk, platform, worker | SSOT, KANONIK | Sandbox parse/convert; iki aşamalı tarama; şüphelide quarantine |
| [KR-080](#kr-080) | Ana İş Akışları için Teknik Kurallar | contracts, edge-kiosk, platform, worker | SSOT, KANONIK | Bu bölüm; ana iş akışlarının iş planı anlatısında zaten bulunan kısımlarını tekrar etmez. Sadece teknik spesifikasyonda eklenen/sertleştirilen kuralları listeler. |
| [KR-081](#kr-081) | Kontrat Şemaları (Contract-First) — Kanonik JSON Schema | contracts, edge-kiosk, platform, worker | SSOT, KANONIK, DEV | *Amaç:** "olmalı" seviyesinden çıkıp, kodlamadan önce ortak dilin **makine-doğrulanabilir** (machine-verifiable) hale gelmesi. |
| [KR-082](#kr-082) | RADIOMETRY / Radyometrik Kalibrasyon (Uyumluluk Etiketi) | contracts, edge-kiosk, platform, worker | SSOT, KANONIK, DEV | Bu madde, **[KR-018] Tam Radyometrik Kalibrasyon Zorunluluğu** ile **aynı zorunluluğu** “KR-082” etiketiyle de referanslayabilmek için eklenmiştir. |
| [KR-083](#kr-083) | İl Operatörü | platform | SSOT, KANONIK, DEV | *Rol Kodu:** ProvinceOperator |

---

## KR detayları

### KR-000

**Başlık:** Bu doküman seti nasıl okunur?  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** Saha adımları ve DJI entegrasyon ayrıntıları ayrı bir SOP dokümanında tutulur

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-001

**Başlık:** Proje Özeti  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Amaç:** Çiftçilerin ürün kaybını erken uyarı ile azaltmak ve dönüm bazlı analiz hizmeti satmak. Başlangıç bölgesi GAP, ardından Türkiye geneline ölçekleme.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-002

**Başlık:** Harita Katmanı Anlamları (Renk + Desen)  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** | Katman | Renk | Desen |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-010

**Başlık:** Web (PWA) - Genel  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** 

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-011

**Başlık:** Kullanıcı Rolleri ve Temel Yaklaşım  
**Applies to:** edge-kiosk, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Rol | Sorumluluk |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-012

**Başlık:** İş Planlaması  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** 

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-013

**Başlık:** Çiftçi Üyeliği ve Tarla Yönetimi  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Üyelik:** PWA veya web üzerinden üye olunur. İl, ilçe, ad, soyad ve telefon numarası alınır; üye olunca kendi sayfasına yönlendirilir.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-014

**Başlık:** Kooperatif/Üretici Birliği Üyeliği ve İşleyiş  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Doğrulama:** Hesap 'Onay Bekliyor' açılır. Evrak kontrolü sonrası Merkez yönetim 'Aktif' yapar; eksik evrak varsa aktif edilemez.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-015

**Başlık:** Drone Pilotları (DJI Mavic 3M ile Uçuş)  
**Applies to:** edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Üyelik/Kayıt:** İl, ilçe, ad soyad, telefon; drone modeli ve seri numarası; hizmet verdiği mahalle/köy listesi (başlangıçta opsiyonel). Drone seri numarası doğrulama referansıdır.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-016

**Başlık:** Drone - Tarla - Bitki Eşleştirme Politikası (Routing)  
**Applies to:** worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Amaç:** Veri setini doğru FieldID ve o tarihte geçerli bitki türü ile eşleştirip doğru bitki-özel YZ modelini otomatik seçmek.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-017

**Başlık:** YZ Modeli ile Analiz (Şemsiye Kural)  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:**
- AnalysisJob semantiği: `FieldID + CropType + MissionID (varsa)`; **PII yok**.
- Edge tarafında model çalıştırılmaz (model theft riski).
- Worker inbound kapalıdır; job **pull/poll** ile kuyruktan alınır; sonuçlar **tek yönlü** yayınlanır.
- KR-017, aşağıdaki KR’lerle operasyonel olarak ayrıştırılır:
  - [KR-070] Worker izolasyonu + egress allowlist (network policy)
  - [KR-071] One-way data flow + allowlist Ingress’te + mTLS cihaz kimliği
  - [KR-072] Dataset lifecycle + chain-of-custody (manifest/hash/signature/verification)
  - [KR-073] Untrusted file handling + AV1/AV2 + sandbox + quarantine
- Kalibrasyon hard gate: [KR-018 / KR-082] sağlanmadan job çalışmaz.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md`
- Platform: bkz. `platform_ssot.md`
- Edge-Kiosk: bkz. `edgekiosk_ssot.md`
- Worker: bkz. `worker_ssot.md`

---
### KR-018

**Başlık:** Tam Radyometrik Kalibrasyon Zorunluluğu (Radiometric Calibration: ışık/sensör etkilerini düzeltme)  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** Model eğitimi (training: modelin öğrenmesi) ve saha sonuçları arasında tutarlılık (training-serving parity: eğitim/çalıştırma aynı dağılım).

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-019

**Başlık:** Expert Portal (Uzman İnceleme)  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** Uzman portalı, modelin düşük güven verdiği veya çelişkili durumlarda manuel inceleme için kullanılır (**PII görünmez**)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-020

**Başlık:** Ücretlendirme  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** 

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-021

**Başlık:** Genel Prensip  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Ücretler bitki türü ve analiz seçeneğine göre: tek seferlik analiz veya yıllık abonelik

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-022

**Başlık:** Fiyat Yönetimi Politikası  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Fiyatlar uygulamada serbest **yazılmaz**; tek kaynak **PriceBook** (Fiyat Kataloğu)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-023

**Başlık:** Örnek Fiyat Kurgusu (Pamuk)  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Seçenek | Liste Fiyat | İlk Yıl / Abonelik Kurgusu |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-024

**Başlık:** Önerilen Tarama Periyodu (Gün)  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Bitki | Önerilen Periyot (gün) |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-025

**Başlık:** Analiz İçeriği (Hizmet Kapsamı)  
**Applies to:** worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Temel İlke:** Sistem ilaçlama kararı **vermez**; yalnızca tespit, risk skoru ve erken uyarı sağlar.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-026

**Başlık:** Sunum Biçimi  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Harita katmanları (ısı haritası / grid / zonlama)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-027

**Başlık:** Abonelik Planlayıcı (Subscription Scheduler)  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, DEV

**Normatif özet:** *Amaç:** Yıllık abonelik seçen kullanıcılar için otomatik, periyodik Mission üretimi.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-028

**Başlık:** Mission Yaşam Döngüsü ve SLA Alanları  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, DEV

**Normatif özet:** *Mission Tanımı:** Bir tarlanın belirli bir tarihte yapılacak tek analiz görevi. Tek seferlik talepten veya yıllık abonelikten oluşabilir.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-029

**Başlık:** YZ Eğitim Geri Bildirimi (Training Feedback Loop)  
**Applies to:** contracts, platform, worker  
**Kaynaklar:** SSOT, DEV

**Normatif özet:** *Amaç:** Uzman düzeltmelerini YZ modeline geri beslemek ve model iyileştirmesi yapmak.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-030

**Başlık:** Notlar, Sınırlar ve Uyum  
**Applies to:** edge-kiosk, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** **Drone standardı:** Başlangıçta DJI Mavic 3M dışında veri kabul edilmez (sonraki fazda değerlendirilir)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-031

**Başlık:** Pilot Hakediş ve Ödeme Politikası  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Pilotlar, bir ay içinde **ONAYLANMIŞ** görevlerde taradıkları alan üzerinden hakediş kazanır

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-032

**Başlık:** Training Export Standardı  
**Applies to:** contracts, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** *Amaç:** Uzman feedback'lerini standart formatta export ederek model eğitim pipeline'ına aktarmak.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-033

**Başlık:** Ödeme ve Manuel Onay (Müşteri Tahsilat Akışı)  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Amaç:** Çiftçi / Kooperatif / Üretici Birliği tarafından açılan **tek seferlik Mission** veya **yıllık Subscription** taleplerinde tahsilatı standartlaştırmak ve talebin “işlenebilir” hale gelmesini …

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-040

**Başlık:** Güvenlik Kabul Kriterleri/Test Checklist (SDLC Entegrasyonu)  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** *Amaç:** TXT repo mantalitesindeki savunma-derinliği (defense-in-depth) güvenlik yaklaşımını, ölçülebilir kabul kriterlerine ve SDLC kapılarına (PR/CI/Release/Ops) bağlamak.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-041

**Başlık:** SDLC Kapıları (Gate) - Zorunlu Kontroller  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Contracts pinleme: CONTRACTS_VERSION (SemVer) + CONTRACTS_SHA256 zorunlu; değişiklikte breaking-change kontrolü

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-042

**Başlık:** Kabul Kriterleri Matrisi  
**Applies to:** edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Güvenlik Katmanı | Kabul Kriteri (DoD) | Test Kanıtı | SDLC Gate |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-043

**Başlık:** Test Checklist (Senaryo Bazlı)  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Senaryo | Adımlar (özet) | Beklenen Sonuç | Kanıt/Artefakt |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-050

**Başlık:** Kimlik Doğrulama ve Üyelik Akışı (Sade Model)  
**Applies to:** worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Kimlik bilgisi olarak yalnızca **Telefon Numarası** kullanılır (E-posta ve TCKN **toplanmaz**)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-060

**Başlık:** Ürün/Teknik Spesifikasyondan Normatif  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** 

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-061

**Başlık:** Amaç ve Sabit Çerçeve  
**Applies to:** platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Drone: DJI Mavic 3M

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-062

**Başlık:** Tasarım İlkeleri  
**Applies to:** edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** 1. **Tek kaynak gerçek:** API ve veri modeli. Web (PWA) iş kuralı kopyalamaz.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-063

**Başlık:** Roller ve Yetkiler (RBAC)  
**Applies to:** edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** | Rol Kodu | Kısa Tanım | Özet Yetki |

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-064

**Başlık:** Harita Katman Standardı (Layer Registry)  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** Katmanlar web (PWA) arayüzünde aynı Layer Registry üzerinden tanımlanır. Renk + desen/ikon + opaklık + öncelik tutarlı olmalıdır.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-065

**Başlık:** Pilot Hakediş Doğrulama (Expected vs Observed)  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** **Expected Area:** FieldBoundary veya Mission flightplan sınırı (m²)

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-066

**Başlık:** Güvenlik ve KVKK  
**Applies to:** edge-kiosk, platform  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** PII ayrı veri alanında tutulur; raporlama ve KPI katmanı pseudonymous kimliklerle çalışır

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-070

**Başlık:** YZ Analiz İzolasyonu (Worker Isolation & Egress Policy)
**Kapsam / Applies-to:** worker

**1) Amaç**
- (Kanonik) Güvenlik ve veri akışı kuralını test edilebilir hale getirmek.

**2) Zorunluluklar (MUST)**
**Kaynaklar:** SSOT, KANONIK

**Normatif kurallar (Hard):**
1) **AI Worker inbound kapalıdır** (deny-by-default). AI Worker (YZ analiz servisi) hiçbir koşulda inbound HTTP kabul etmez.
   **Ingest Gateway ayrımı:** Sunucu 2’deki Ingest Gateway ayrı bir bileşendir (ayrı konteyner/pod, ayrı network policy). Yalnızca M2 allowlist IP + mTLS ile sınırlı inbound kabul eder. Ingest Gateway ile AI Worker arasında konteyner düzeyinde izolasyon zorunludur.
2) Worker job’ı **pull/poll** ile alır (queue/dispatch). Platform→Worker push **yok**.  
3) Worker egress **allowlist** ile sınırlıdır:  
   - Object Storage (S3-uyumlu) → **read-only**  
   - Queue/Dispatch → **consume-only**  
   - Observability → **append-only**  
   - Internet → **DENY**  
4) Worker job çalıştırmadan önce **precondition** doğrular:  
   - `CALIBRATED` kanıtı (**[KR-018]**)  
   - manifest/hash/(varsa signature) + AV raporları + verification (**[KR-072]**, **[KR-073]**)  
5) Ops erişimi: bastion + MFA + JIT; yönetim portları public internete açılmaz.

**Network Policy Matrix:**
- Platform → Worker: **DENY**
- Web/PWA → Worker: **DENY**
- Worker → Storage/Queue/Results/Observability: **ALLOW (outbound only, mTLS)**
- Worker → Internet: **DENY**
- M2 (EdgeKiosk) → Ingest Gateway: **ALLOW (inbound, allowlist IP + mTLS)**
- Ingest Gateway → AI Worker: **DENY (pod-to-pod)**

**Audit/WORM olayları (minimum):**
- `SECURITY.DENY`, `JOB.REJECT`, `DATASET.REJECTED_QUARANTINE`

**SDLC Gate / Test (minimum):**
- Policy deny test (platform→worker TCP)  
- Calibrated yok → job reject  
- Hash mismatch → quarantine  
- Contracts CI validate + breaking-change detector (**[KR-081]**)

---

**4) Kanıt / Artefact**
- Üretilen raporlar/manifestler/sertifikalar ve referanslar (KR-072/KR-073 ile).

**5) Audit / Log**
- SECURITY.DENY / JOB.REJECT / HASH.MISMATCH vb. olaylar; correlation_id zorunlu.

**6) Hata Modları / Quarantine**
- Şüpheli/tamper/malware → REJECTED_QUARANTINE; işlem durur ve kanıt üretilir.

**7) Test / Kabul Kriterleri**
- Negatif testler: inbound denemeleri reddedilir; eksik kanıtla job reddedilir; hash mismatch yakalanır.

**8) Cross-refs**
- KR-017 (şemsiye), KR-018 (kalibrasyon), KR-070..KR-073 (akış/kanıt).

---
### KR-071

**Başlık:** Tek Yönlü Veri Akışı + Allowlist Yerleşimi (One-way Data Flow)
**Kapsam / Applies-to:** edge-kiosk, platform, worker

**1) Amaç**
- (Kanonik) Güvenlik ve veri akışı kuralını test edilebilir hale getirmek.

**2) Zorunluluklar (MUST)**
**Kaynaklar:** SSOT, KANONIK

**Kanonik akış (Hard):**
1) EdgeKiosk → Platform/Ingress: HTTPS 443 + **mTLS cihaz kimliği** (client cert).  
2) Platform: ham veriyi public API’de servis etmez; storage + queue üzerinden orkestrasyon yapar.  
3) Worker: queue/storage’dan **pull** eder; analiz eder.  
4) Worker → Platform: sadece **türev sonuç** (AnalysisResult/layers) yazar.  
5) Web/PWA: sadece sonuç okur; ham veri **yok**.

**Allowlist yerleşimi:**
- IP allowlist **kimlik değildir** (dinamik IP/CGNAT).  
- Allowlist yalnızca **Ingress kapısında** ikincil katmandır. Ana kontrol **mTLS**’tir.

**SDLC Test (minimum):**
- allowlist dışı IP → deny + audit
- sertifikasız istek → deny + audit
- worker’a direct HTTP → deny (policy)

**Platform Uygulama Notu — Depolama stratejisi (pre-signed URL):**
Platform büyük veri dosyalarını relay etmez.
EdgeKiosk manifest JSON gönderir, Platform pre-signed upload URL üretir, EdgeKiosk
doğrudan S3 quarantine-bucket’a yazar. Tek yönlü veri akışı ilkesi Platform→Worker
için de geçerlidir: Sunucu 2 (Data Pipeline) hiçbir zaman Sunucu 1’e (Platform Core)
HTTP isteği atmaz. İletişim yalnızca PostgreSQL write + RabbitMQ event üzerinden yapılır.
Sunucu 1’in IP/port bilgisi Sunucu 2’de tanımlı değildir.
(Detay: bkz. `docs/architecture/data_lifecycle_transfer.md`)

---

**4) Kanıt / Artefact**
- Üretilen raporlar/manifestler/sertifikalar ve referanslar (KR-072/KR-073 ile).

**5) Audit / Log**
- SECURITY.DENY / JOB.REJECT / HASH.MISMATCH vb. olaylar; correlation_id zorunlu.

**6) Hata Modları / Quarantine**
- Şüpheli/tamper/malware → REJECTED_QUARANTINE; işlem durur ve kanıt üretilir.

**7) Test / Kabul Kriterleri**
- Negatif testler: inbound denemeleri reddedilir; eksik kanıtla job reddedilir; hash mismatch yakalanır.

**8) Cross-refs**
- KR-017 (şemsiye), KR-018 (kalibrasyon), KR-070..KR-073 (akış/kanıt).

---
### KR-072

**Başlık:** Dataset Lifecycle + Kanıt Zinciri (Chain of Custody) — Contract-First
**Kapsam / Applies-to:** contracts, edge-kiosk, platform, worker

**1) Amaç**
- (Kanonik) Güvenlik ve veri akışı kuralını test edilebilir hale getirmek.

**2) Zorunluluklar (MUST)**
**Kaynaklar:** SSOT, KANONIK

**Dataset durumları (minimum):**
`RAW_INGESTED` → `RAW_SCANNED_EDGE_OK` → `RAW_HASH_SEALED` → `CALIBRATED` (**[KR-018]**) →  
`CALIBRATED_SCANNED_CENTER_OK` → `DISPATCHED_TO_WORKER` → `ANALYZED` → `DERIVED_PUBLISHED` → `ARCHIVED`  
Hata/şüphe: `REJECTED_QUARANTINE`

**Zorunlu kanıt artefact’leri:**
- `dataset_manifest.json` + `manifest.sha256` + (opsiyonel) `signature.sig`
- `scan_report_edge.json` (AV1)
- `scan_report_center.json` (AV2)
- `verification_report.json` (hash match/mismatch)
- `calibration_result.json` + `qc_report.json`
- `evidence_bundle_ref` (platform sonuçlarında sadece referans)

**Hard gate:**
- Hash mismatch / AV fail / QC fail → `REJECTED_QUARANTINE`
- `CALIBRATED_SCANNED_CENTER_OK` olmadan Worker job kabul etmez.

**Contract-first:**
- Şemalar `tarlaanaliz-contracts` altında JSON Schema + örnekler + CI doğrulama (**[KR-081]**)

---

**4) Kanıt / Artefact**
- Üretilen raporlar/manifestler/sertifikalar ve referanslar (KR-072/KR-073 ile).

**5) Audit / Log**
- SECURITY.DENY / JOB.REJECT / HASH.MISMATCH vb. olaylar; correlation_id zorunlu.

**6) Hata Modları / Quarantine**
- Şüpheli/tamper/malware → REJECTED_QUARANTINE; işlem durur ve kanıt üretilir.

**7) Test / Kabul Kriterleri**
- Negatif testler: inbound denemeleri reddedilir; eksik kanıtla job reddedilir; hash mismatch yakalanır.

**8) Cross-refs**
- KR-017 (şemsiye), KR-018 (kalibrasyon), KR-070..KR-073 (akış/kanıt).

---
### KR-073

**Başlık:** Untrusted File Handling + AV1/AV2 + Sandbox Dönüştürme
**Kapsam / Applies-to:** edge-kiosk, platform, worker

**1) Amaç**
- (Kanonik) Güvenlik ve veri akışı kuralını test edilebilir hale getirmek.

**2) Zorunluluklar (MUST)**
**Kaynaklar:** SSOT, KANONIK

**Normatif kurallar (Hard):**
- Ham dosyalar (TIFF/JPEG/RAW vb.) **untrusted input** kabul edilir. Parse/convert işlemleri sandbox’ta yapılır.
- **AV1 (EdgeKiosk)** ön filtredir; yerel istasyonu korur ve bariz zararlıyı erken yakalar.
- **AV2 (Merkez Security Gateway)** platform tarafında karar veren taramadır; çalışma modu `scan_policy` parametresine bağlıdır (aşağıya bkz.).
- Hash doğrulama + dosya tipi whitelist kontrolü **her modda zorunludur** ve asla atlanamaz.
- Güvenli türev (tiles/COG/thumbnail) üretimi merkezde sandbox işçisinde yapılır; platform public ham servis etmez.

**Platform Tarama Politikası (`scan_policy`) — İki Modlu AV2 Tarama:**
EdgeKiosk’taki AV1 taraması ön filtredir; platform tarafındaki AV2 karar veren taramadır.
CENTRAL_ADMIN `scan_policy` parametresi ile aşağıdaki modlar arasında geçiş yapabilir:

**MOD 1 — SMART (varsayılan):**
Normal operasyonda aktif olan moddur. Dosyalar quarantine-bucket’a ulaştığında
sistem önce hafif doğrulama yapar (SHA-256 hash + dosya tipi whitelist kontrolü).
Tam AV taraması SADECE şu tetikleyici koşullardan biri varsa çalışır:
  - Dosya boyutu manifest’teki beklenen değerden ±%20 sapıyorsa
  - Dosya uzantısı izin verilen whitelist dışındaysa
  - SHA-256 hash manifest ile uyuşmuyorsa
  - `drone_id` sistem tarafından ilk kez görülüyorsa
  - EdgeKiosk yazılım sürümü güncel değilse (minimum versiyon kontrolü)

Bu koşulların hiçbiri yoksa dosya sadece hash doğrulama + dosya tipi kontrolünden
geçer (AV taraması atlanır). Düzenli çalışan bilinen drone’lardan gelen standart
görüntü dosyalarının büyük çoğunluğu hafif yoldan geçer. Bu mod operasyonel
maliyeti dramatik şekilde düşürür.

**MOD 2 — BYPASS (istisna — KR-073’ü geçersiz kılmaz):**
AV taraması tamamen devre dışıdır. Sadece SHA-256 hash doğrulama ve dosya tipi
kontrolü yapılır. BYPASS bir istisnadır ve KR-073’ün temel güvenlik garantilerini
geçersiz kılmaz.

BYPASS kuralları:
  - Yalnızca **CENTRAL_ADMIN** tarafından etkinleştirilebilir
  - **Coğrafi sınırlama zorunlu:** il bazında (`province_code`) belirtilmeli; kapsam dışı iller SMART modda çalışmaya devam eder
  - **Zamansal sınırlama zorunlu:** tarih/saat aralığı belirtilmeli
  - Maksimum süre sınırı: 72 saat — süre dolduğunda sistem otomatik olarak SMART moduna döner
  - Etkinleştirildiğinde audit log’a zorunlu kayıt: kim, ne zaman, neden, hangi iller, süre
  - BYPASS aktifken admin dashboard’da kırmızı uyarı banner’ı görünür
  - BYPASS süresi CENTRAL_ADMIN tarafından uzatılabilir ama her uzatma ayrı audit kaydı oluşturur
  - Başlangıç kapsamı: Diyarbakır + CENTRAL_ADMIN’in belirlediği iller

**İl Bazlı Zorunlu AV Tarama (CENTRAL_ADMIN Override):**
CENTRAL_ADMIN, belirli bir ilin (`province_code`) verileri için `scan_policy` değerini
**MANDATORY** olarak ayarlayabilir. Bu durumda ilgili ilden gelen tüm datasetlere
mevcut global mod ne olursa olsun (SMART veya BYPASS) tam AV2 taraması uygulanır.
  - İl bazlı MANDATORY ayarı global modu **override** eder
  - Birden fazla il aynı anda MANDATORY olarak işaretlenebilir
  - İl bazlı ayar değişiklikleri audit log’a kaydedilir

**Her iki modda da geçerli sabit kurallar:**
- Hash doğrulama **ASLA** atlanamaz (her modda zorunlu)
- Dosya tipi whitelist kontrolü **ASLA** atlanamaz (her modda zorunlu)
- `verified-bucket`’a geçiş ancak ilgili modun tüm kontrolleri başarılıysa olur

**Quarantine:**
- AV fail / hash mismatch / QC fail → `REJECTED_QUARANTINE` + audit.

**SDLC Test (minimum):**
- (Lab) EICAR tetiklemesi
- AV1 PASS ama AV2 FAIL → quarantine
- Sandbox crash olmadan kontrollü hata
- scan_policy=SMART + anomali yok → AV atlanır, hash + whitelist geçer
- scan_policy=SMART + boyut sapması → tam AV tetiklenir
- scan_policy=BYPASS + 72 saat aşımı → otomatik SMART’a dönüş
- BYPASS etkinleştirme → audit log kaydı zorunlu
- İl bazlı MANDATORY + global BYPASS → ilgili il verilerine tam AV uygulanır

---

**4) Kanıt / Artefact**
- Üretilen raporlar/manifestler/sertifikalar ve referanslar (KR-072/KR-073 ile).
- `scan_policy_change` audit kaydı (mod değişikliklerinde)

**5) Audit / Log**
- SECURITY.DENY / JOB.REJECT / HASH.MISMATCH vb. olaylar; correlation_id zorunlu.
- SCAN_POLICY.CHANGE / SCAN_POLICY.BYPASS_ENABLE / SCAN_POLICY.BYPASS_EXPIRE / SCAN_POLICY.PROVINCE_MANDATORY olayları.

**6) Hata Modları / Quarantine**
- Şüpheli/tamper/malware → REJECTED_QUARANTINE; işlem durur ve kanıt üretilir.
- BYPASS süresi dolduğunda otomatik SMART’a dönüş; açık kalan dosyalar SMART kurallarıyla yeniden değerlendirilir.

**7) Test / Kabul Kriterleri**
- Negatif testler: inbound denemeleri reddedilir; eksik kanıtla job reddedilir; hash mismatch yakalanır.
- BYPASS → 72h aşımı → otomatik SMART geçişi doğrulanır.
- İl bazlı MANDATORY override doğrulanır.

**8) Cross-refs**
- KR-017 (şemsiye), KR-018 (kalibrasyon), KR-070..KR-073 (akış/kanıt).

---
### KR-080

**Başlık:** Ana İş Akışları için Teknik Kurallar  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK

**Normatif özet:** Bu bölüm; ana iş akışlarının iş planı anlatısında zaten bulunan kısımlarını tekrar etmez. Sadece teknik spesifikasyonda eklenen/sertleştirilen kuralları listeler.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-081

**Başlık:** Kontrat Şemaları (Contract-First) — Kanonik JSON Schema  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** *Amaç:** "olmalı" seviyesinden çıkıp, kodlamadan önce ortak dilin **makine-doğrulanabilir** (machine-verifiable) hale gelmesi.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-082

**Başlık:** RADIOMETRY / Radyometrik Kalibrasyon (Uyumluluk Etiketi)  
**Applies to:** contracts, edge-kiosk, platform, worker  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** Bu madde, **[KR-018] Tam Radyometrik Kalibrasyon Zorunluluğu** ile **aynı zorunluluğu** “KR-082” etiketiyle de referanslayabilmek için eklenmiştir.

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
### KR-083

**Başlık:** İl Operatörü  
**Applies to:** platform  
**Kaynaklar:** SSOT, KANONIK, DEV

**Normatif özet:** *Rol Kodu:** ProvinceOperator

**Component dokümanları:**
- Contracts: bkz. `contracts_ssot.md` (bu KR contracts kapsamındaysa)
- Platform: bkz. `platform_ssot.md` (bu KR platform kapsamındaysa)
- Edge-Kiosk: bkz. `edgekiosk_ssot.md` (bu KR edge-kiosk kapsamındaysa)
- Worker: bkz. `worker_ssot.md` (bu KR worker kapsamındaysa)

---
