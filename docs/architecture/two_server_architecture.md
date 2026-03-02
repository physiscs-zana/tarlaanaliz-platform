BOUND: TARLAANALIZ_SSOT_v1_0_0.txt – canonical rules are referenced, not duplicated.

# Title
İki Sunucu Mimarisi — Platform Core + Data Pipeline

## Scope
Platform'un fiziksel iki sunucuya bölünme gerekçesini, bileşen yerleşimini, veritabanı
rol ayrımını, servisler arası iletişim kurallarını ve mevsimsel ölçekleme stratejisini
tanımlar. Veri akışı detayları `data_lifecycle_transfer.md`'de kanonik olarak
tanımlanmıştır; bu doküman **dağıtım topolojisini** belirler.

## Owners
- Staff Backend Architect
- Security Lead
- DevOps Lead

## Last updated
2026-03-01

## SSOT references
- KR-070 (Worker Isolation & Egress Policy)
- KR-071 (One-way Data Flow + Allowlist Yerleşimi)
- KR-072 (Dataset Lifecycle + Chain of Custody)
- KR-073 (Untrusted File Handling + AV1/AV2 + Sandbox)
- KR-081 (Contract-First / Schema Gates)
- KR-033 (Ödeme + Manuel Onay)
- KR-063 (Roller ve Yetkiler — RBAC)
- KR-050 (Kimlik Doğrulama)
- KR-018 (Radiometric Calibration Hard Gate)
- KR-030 (Drone Registry)
- KR-015 (Pilot Kapasite/Planlama)
- KR-028 (Mission Yaşam Döngüsü + SLA)
- KR-029 (YZ Eğitim Geri Bildirimi)

---

## Terminoloji

| Terim | Ne demek | Nerede |
|-------|----------|--------|
| M1 | İşleme İstasyonu | Edge / fiziksel |
| M2 | Koordinatör + Kanıt İstasyonu | Edge / fiziksel |
| Sunucu 1 | Platform Core | Cloud |
| Sunucu 2 | Data Pipeline | Cloud |
| Platform | Sunucu 1 + Sunucu 2 | Cloud |
| EdgeKiosk | M1 + M2 | Edge |
| Worker | YZ analiz servisi | Cloud (Sunucu 2 içi) |

---

## §1 Bölme Gerekçesi

Platform, mantıksal olarak iki farklı sorumluluk alanına ayrılır. Bu ayrım üç ana
nedenle fiziksel sunucu düzeyine yükseltilmiştir:

### 1.1 Güvenlik İzolasyonu
Sunucu 2 (Data Pipeline) **güvenilmez dosyalar** işler: AV2 tarama, hash doğrulama,
sandbox dönüşüm (KR-073). Bu sunucu ele geçirilse bile kullanıcı PII verisine,
ödeme bilgilerine ve RBAC tablolarına **erişemez** (DB role ayrımı, bkz. §4).

### 1.2 Ters Orantılı Ölçekleme
- **Sunucu 1** yükü kullanıcı sayısıyla orantılıdır (API, SSR, auth) — düz büyüme.
- **Sunucu 2** yükü aktif drone sayısı ve uçuş sezonu ile orantılıdır — mevsimsel
  patlama (bkz. §8). Pipeline 3–5× büyürken Platform Core aynı kalabilir.

### 1.3 KR-071 Uyumu
SSOT [KR-071] tek yönlü veri akışını zorunlu kılar. Mantıksal ayrım, ağ katmanında
fiziksel ayrıma yükseltilerek "varsayılan reddet" (deny-by-default) güvencesi
güçlendirilmiştir: Sunucu 2'de AI Worker genel internete kapalıdır (KR-070);
Ingest Gateway yalnızca M2 allowlist IP + mTLS ile sınırlı inbound kabul eder.

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                         DAĞITIM TOPOLOJİSİ                              │
  │                                                                          │
  │  ┌────────────────────────┐         ┌────────────────────────┐          │
  │  │  SUNUCU 1              │         │  SUNUCU 2              │          │
  │  │  Platform Core         │         │  Data Pipeline         │          │
  │  │                        │         │                        │          │
  │  │  ● Kullanıcı-facing    │         │  ● Dosya işleme        │          │
  │  │  ● API + SSR           │         │  ● AV2 + hash verify   │          │
  │  │  ● Auth + RBAC         │         │  ● AI Worker           │          │
  │  │  ● Ödeme + SLA         │         │  ● Ingest Gateway      │          │
  │  │                        │         │                        │          │
  │  │  İnternet: AÇIK        │         │  Inbound: M2 allowlist │          │
  │  │  (Cloudflare arkası)   │         │  + mTLS ONLY           │          │
  │  └───────────┬────────────┘         └───────────┬────────────┘          │
  │              │                                   │                       │
  │              └──────────┬──────────┬─────────────┘                       │
  │                         │          │                                     │
  │                    ┌────▼──┐  ┌────▼───┐                                │
  │                    │  DB   │  │RabbitMQ│                                │
  │                    │(PgSQL)│  │(Queue) │                                │
  │                    └───────┘  └────────┘                                │
  │                                                                          │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## §2 Sunucu 1 — Platform Core

Kullanıcıya dönük tüm servisleri barındırır. İnternet erişimi Cloudflare üzerinden
filtrelenir.

### Bileşenler

| Bileşen | KR Ref | Açıklama |
|---------|--------|----------|
| FastAPI API | KR-081 | Kullanıcı-facing API endpoint'leri (`/api/v1/*`) |
| Next.js SSR/Frontend | — | Web arayüzü + PWA |
| Scheduler (cron) | KR-015 | Abonelik takvimi, mission planlama, yeniden zamanlama |
| Payment SM | KR-033 | Ödeme durum makinesi (PENDING → PAID → ... ) |
| Expert Portal | KR-029 | Uzman inceleme arayüzü |
| RBAC / Auth | KR-063, KR-050 | 12 kanonik rol + 2 yeni (STATION_OPERATOR, BILLING_ADMIN), JWT, brute-force koruması |
| Pilot Planner | KR-015 | Seed+Pull iş dağıtım, kapasite yönetimi |
| SLA Monitor | KR-028 | Mission SLA takibi, breach alarm |
| Training Feedback API | KR-029 | YZ eğitim geri bildirim toplama (portal tarafı) |
| Bildirimler | KR-033 | SMS + uygulama içi bildirim (ödeme, mission, SLA) |

> **Not:** Ingest endpoint (`POST /api/v1/edge/ingest`) Sunucu 1'de değil,
> **Sunucu 2'dedir** (bkz. §3). M2 (EdgeKiosk) saha cihaz trafiği Sunucu 1'e
> ulaşmaz — bu, saha cihazı saldırı yüzeyinden kullanıcı PII/ödeme verilerinin
> izolasyonunu sağlar.

### Kaynak Profili

| Metrik | Değer |
|--------|-------|
| CPU | Hafif, sürekli (API/SSR) |
| RAM | 4–8 GB (Redis dahil) |
| Ölçekleme ekseni | Kullanıcı sayısı |
| Ağ | İnternet + Cloudflare |

---

## §3 Sunucu 2 — Data Pipeline

Güvenilmez dosya işleme, ingest gateway, AV2 tarama ve YZ analiz iş yüklerini
barındırır. AI Worker'ın internete açık endpoint'i yoktur. Ingest Gateway yalnızca
M2 (EdgeKiosk) allowlist IP + mTLS ile sınırlı inbound kabul eder (KR-070).

### Bileşenler

| Bileşen | KR Ref | Açıklama |
|---------|--------|----------|
| **Ingest Gateway** (ayrı pod) | KR-071, KR-072 | M2'den manifest JSON alır, doğrular, presigned S3 URL üretir. Yalnızca M2 allowlist IP + mTLS |
| SMART/BYPASS Mod Yöneticisi | KR-073 | `scan_policy` parametresine göre AV2'yi koşullu tetikler |
| S3 Event Listener | KR-072 | Quarantine-bucket'a yeni dosya geldiğinde pipeline'ı tetikler |
| AV2 Scanner (sandbox) | KR-073 | Merkez antivirüs taraması, **ayrı konteyner** içinde çalışır (DB bağlantısı yok) |
| Hash Verifier (SHA-256) | KR-072 | Manifest'teki hash ile S3 nesnesinin hash'ini karşılaştırır |
| Evidence Bundle Builder | KR-072 | `scan_report_center.json` + `verification_report.json` paketler |
| Quarantine → Verified Mover | KR-073 | Tüm kontroller PASS → dosyaları S3 verified-bucket'a taşır (S3 COPY) |
| AI Worker (YZ analiz, ayrı pod) | KR-070 | RabbitMQ'dan job alır (pull/poll), verified-bucket'tan dataset okur (read-only, mTLS) |
| Drone Registry Cache | KR-030 | Kayıtlı drone metadata'sının yerel kopyası (doğrulama amaçlı) |

> **Not:** Kalibrasyon yalnızca M1 (Edge) tarafındadır. Sunucu 2'ye kalibrasyon
> sorumluluğu verilmez (Karar 6). Worker, job çalıştırmadan önce `CALIBRATED`
> kanıtını dataset metadata'sından doğrular (KR-018 hard gate).

### Ingest Akışı (M2 → Sunucu 2)

```
M2 (EdgeKiosk)               Sunucu 2 (Ingest Gateway)         S3
   │                              │                               │
   │  POST /edge/ingest          │                               │
   │  (manifest JSON, <1KB)      │                               │
   │  mTLS + allowlist           │                               │
   │─────────────────────────────►│                               │
   │                              │  manifest hash doğrula        │
   │                              │  drone_id → registry (KR-030) │
   │                              │  presigned URL üret            │
   │  200 OK                      │                               │
   │  {upload_urls, session_id}   │                               │
   │◄─────────────────────────────│                               │
   │                              │                               │
   │  HTTP PUT (presigned URL)    │                               │
   │  ham dosyalar (~1 TB)        │                               │
   │──────────────────────────────┼──────────────────────────────►│
   │                              │                               │
   │                              │  S3 Event Notification        │
   │                              │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ──►│
   │                              │                  Pipeline tetikler
```

### Pipeline İş Akışı (Event-Driven)

```
                            ┌───────────────────────────────────────────┐
                            │          SUNUCU 2 — PİPELİNE AKIŞI       │
                            │                                           │
S3 quarantine               │  ┌─────────────┐   ┌──────────────┐     │
Event Notification ────────►│  │ scan_policy  │──►│ AV2 Scanner  │     │
                            │  │ (SMART/      │   │ (sandbox)    │     │
                            │  │  BYPASS)     │   └──────┬───────┘     │
                            │  └─────────────┘          │              │
                            │        │ hafif yol         │ tam tarama   │
                            │        ▼                   ▼              │
                            │  ┌──────────────────────────────┐        │
                            │  │ Hash Verifier (SHA-256)      │        │
                            │  │ + Dosya Tipi Whitelist       │        │
                            │  └──────────────┬───────────────┘        │
                            │                 │                        │
                            │      ┌──────────▼──────────┐            │
                            │      │ Evidence Bundle     │            │
                            │      │ Builder (KR-072)    │            │
                            │      └──────────┬──────────┘            │
                            │                 │                        │
                            │            ALL PASS?                     │
                            │           /        \                     │
                            │          ▼          ▼                    │
                            │  ┌──────────┐  ┌────────────┐           │
                            │  │ S3 COPY  │  │ REJECTED   │           │
                            │  │ verified │  │ QUARANTINE │           │
                            │  └──────────┘  └────────────┘           │
                            │                                          │
  RabbitMQ                  │  ┌──────────┐    ┌──────────────┐       │
  job dispatch ────────────►│  │ AI Worker│───►│ DB write:    │       │
  (pull/poll)               │  │ (YZ)     │    │ analysis_jobs│       │
                            │  └──────────┘    │ .status =    │       │
                            │                  │ 'ANALYZED'   │       │
                            │                  └──────────────┘       │
                            └──────────────────────────────────────────┘
```

### Bileşen İzolasyonu

**Ingest Gateway** (ayrı pod): M2'den manifest alır, presigned URL üretir. AI Worker
ile **pod-to-pod ağ trafiği DENY** (KR-070). Genel internetten erişilemez — yalnızca
M2 allowlist IP + mTLS.

**AI Worker** (ayrı pod): SSOT [KR-070] gereği **inbound HTTP kabul etmez**. İş alma
yalnızca RabbitMQ pull/poll ile olur.

**Paylaşılan DB modeli:** Worker sonucu doğrudan `analysis_jobs` tablosuna yazar.
Platform (Sunucu 1) CQRS query handler'ları ile DB'yi okur. Bu, KR-070'in "tek yönlü
sonuç akışı" amacını korurken sunucular arası HTTP bağımlılığını ortadan kaldırır.

### Kaynak Profili

| Metrik | Değer |
|--------|-------|
| CPU | Yoğun, anlık artış (AV2 tarama + YZ analiz) |
| RAM | 8–16 GB (AV motor + büyük dosya buffer) |
| Ölçekleme ekseni | Drone sayısı / uçuş sezonu |
| Ağ | İnternet ERİŞİLEMEZ — yalnızca iç ağ (S3, DB, Queue) |

---

## §4 Paylaşılan Veritabanı Katmanı

İki sunucu **aynı PostgreSQL instance'ını** paylaşır. Güvenlik ayrımı, veritabanı
rolleri (ROLE) ve tablo düzeyinde GRANT/REVOKE ile sağlanır.

### DB Role Erişim Matrisi

```
┌────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Role Erişim Matrisi                   │
│                                                                    │
│  ROLE: platform_core_rw                                            │
│  ├── users ──────────────── SELECT, INSERT, UPDATE                 │
│  ├── user_roles ─────────── SELECT, INSERT, UPDATE, DELETE         │
│  ├── cooperatives ───────── SELECT, INSERT, UPDATE                 │
│  ├── coop_memberships ───── SELECT, INSERT, UPDATE, DELETE         │
│  ├── fields ─────────────── SELECT, INSERT, UPDATE                 │
│  ├── field_crops ────────── SELECT, INSERT, UPDATE                 │
│  ├── missions ───────────── SELECT, INSERT, UPDATE                 │
│  ├── subscriptions ──────── SELECT, INSERT, UPDATE                 │
│  ├── price_snapshots ────── SELECT, INSERT                         │
│  ├── payment_intents ────── SELECT, INSERT, UPDATE                 │
│  ├── analysis_jobs ──────── SELECT, INSERT, UPDATE                 │
│  ├── calibration_records ── SELECT, INSERT, UPDATE                 │
│  ├── qc_reports ─────────── SELECT, INSERT, UPDATE                 │
│  ├── audit_logs ─────────── SELECT, INSERT (WORM: UPDATE/DELETE ✗) │
│  └── mission_route_files ── SELECT, INSERT, UPDATE                 │
│                                                                    │
│  ROLE: pipeline_rw                                                 │
│  ├── analysis_jobs ──────── SELECT, INSERT, UPDATE                 │
│  ├── calibration_records ── SELECT, INSERT, UPDATE                 │
│  ├── qc_reports ─────────── SELECT, INSERT, UPDATE                 │
│  ├── audit_logs ─────────── INSERT (WORM: yalnızca yazma)          │
│  ├── missions ───────────── SELECT (status okuma amaçlı)           │
│  └── drone_registry ─────── SELECT (teknik tablo, doğrulama)       │
│                                                                    │
│  pipeline_rw ERİŞEMEZ:                                             │
│  ✗ users                                                           │
│  ✗ user_roles                                                      │
│  ✗ cooperatives                                                    │
│  ✗ coop_memberships                                                │
│  ✗ subscriptions                                                   │
│  ✗ payment_intents                                                 │
│  ✗ price_snapshots                                                 │
│  ✗ fields (PII: konum + sahip bilgisi)                             │
│  ✗ field_crops                                                     │
│  ✗ pilot_profiles                                                  │
│  ✗ user_pii                                                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Ek Katmanlar

| Bileşen | Kullanım | Notlar |
|---------|----------|--------|
| Redis | Cache + rate-limit | Sunucu 1'de birincil; Sunucu 2 gerekirse kendi instance'ı |
| RabbitMQ | İş dağıtımı (broker) | Sunucu 1 → publish, Sunucu 2 → consume (KR-070: pull/poll) |

---

## §5 Servisler Arası İletişim

**Temel ilke:** Microservice DEĞİL — paylaşımlı DB ile dikey yeterlilik
(shared-database modular monolith + isolated pipeline).

### İletişim Matrisi

```
┌──────────┐                                           ┌──────────┐
│ Sunucu 1 │                                           │ Sunucu 2 │
│ Platform │                                           │ Pipeline │
│          │                                           │          │
│  publish ├────────── RabbitMQ ──────────────────────►│ consume  │
│  (job)   │           (queue)                         │ (pull)   │
│          │                                           │          │
│  SELECT  │◄────────── PostgreSQL ───────────────────►│ INSERT/  │
│  (CQRS   │           (shared DB)                     │ UPDATE   │
│   read)  │                                           │ (write)  │
│          │                                           │          │
│  LISTEN  │◄────────── PG NOTIFY ────────────────────│ NOTIFY   │
│  (real-  │           (kanal)                         │ (event)  │
│   time)  │                                           │          │
│          │           ┌─────────┐                     │          │
│          │           │   S3    │◄────────────────────┤ read/    │
│          │           │ buckets │                     │ write/   │
│          │           └─────────┘                     │ presign  │
└──────────┘                                           └──────────┘

     ✗ Sunucu 2 → Sunucu 1: HTTP çağrısı YOK
     ✗ Sunucu 1 → Sunucu 2: Doğrudan TCP/HTTP YOK (KR-070: platform→worker DENY)
```

### Akış Kuralları

1. **Sunucu 1 → RabbitMQ → Sunucu 2:** İş bildirimi (dispatch). Sunucu 2 pull/poll
   ile alır. Sunucu 1 asla Sunucu 2'ye doğrudan push yapmaz (KR-070).
2. **Sunucu 2 → PostgreSQL:** Pipeline tamamlandığında sonuçları DB'ye yazar
   (`analysis_jobs.status = 'ANALYZED'`, `qc_reports`, `calibration_records`).
3. **Sunucu 1 ← PostgreSQL:** Platform, CQRS query handler'ları ile DB'yi okur.
4. **Gerçek zamanlı bildirim:** Sunucu 2 `NOTIFY pipeline_done, '{"job_id": "..."}'`
   gönderir. Sunucu 1 `LISTEN pipeline_done` ile anında haberdar olur.
5. **S3 Event → Sunucu 2:** Quarantine-bucket'a dosya geldiğinde S3, event
   notification ile Sunucu 2'nin pipeline'ını tetikler.
6. **HTTP çağrısı: HİÇBİR ZAMAN** — Ne Sunucu 2→Sunucu 1 ne de Sunucu 1→Sunucu 2
   yönünde doğrudan HTTP bağlantısı kurulmaz. Tüm iletişim DB, queue ve S3 event
   kanalları üzerinden gerçekleşir.

---

## §6 Güvenlik Kuralları

### Ağ Erişim Matrisi

| Kaynak → Hedef | Protokol | İzin | KR Ref |
|----------------|----------|------|--------|
| İnternet → Sunucu 1 | HTTPS 443 | Cloudflare WAF arkası | — |
| M2 (EdgeKiosk) → Sunucu 2 (Ingest Gateway) | HTTPS + mTLS | Allowlist IP (ikincil) + mTLS (birincil) | KR-071 |
| M2 (EdgeKiosk) → S3 quarantine | HTTPS (presigned PUT) | Presigned URL ile | KR-072 |
| İnternet → Sunucu 2 (AI Worker) | TCP * | **DENY** (tüm portlar) | KR-070 |
| Ingest Gateway → AI Worker | Pod-to-pod | **DENY** (konteyner izolasyonu) | KR-070 |
| Sunucu 1 → Sunucu 2 | TCP/HTTP | **DENY** | KR-070 |
| Sunucu 2 → Sunucu 1 | TCP/HTTP | **DENY** | KR-070 |
| Sunucu 2 → S3 (quarantine) | HTTPS | READ (AV2 + hash verify) | KR-073 |
| Sunucu 2 → S3 (verified) | HTTPS | WRITE (taşıma) | KR-072 |
| Sunucu 2 → S3 (verified) | HTTPS | READ (AI Worker, read-only, mTLS + kısa ömürlü token) | KR-070 |
| Sunucu 2 → PostgreSQL | TCP 5432 | `pipeline_rw` rolü | §4 |
| Sunucu 2 → RabbitMQ | AMQP | consume-only | KR-070 |

### Sunucu 2 İç Pod İzolasyonu (KR-070, KR-073)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Sunucu 2 — Üç İzole Pod                                            │
│                                                                      │
│  ┌──────────────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│  │ Ingest Gateway   │  │ Pipeline      │  │ AV2 Sandbox           │ │
│  │ Pod              │  │ Orchestrator  │  │ (ayrı konteyner)      │ │
│  │                  │  │ Pod           │  │                       │ │
│  │ Inbound:         │  │               │  │ ● DB bağlantısı YOK  │ │
│  │  M2 allowlist+   │  │ ● DB bağlantı │  │ ● Ağ: sadece S3 read │ │
│  │  mTLS ONLY       │  │ ● Queue erişim│  │ ● /tmp/sandbox/ lokal│ │
│  │                  │  │ ● S3 erişim   │  │ ● Çıktı: scan_report │ │
│  │ Outbound:        │  │               │  │                       │ │
│  │  S3 (presigned)  │  │        ──────►│  │◄──── tetikle          │ │
│  │  PostgreSQL      │  │        ◄──────│  │────► rapor döndür     │ │
│  │  RabbitMQ        │  │               │  │                       │ │
│  │                  │  │               │  │                       │ │
│  │ → AI Worker: ✗   │  │               │  │                       │ │
│  └──────────────────┘  └───────────────┘  └───────────────────────┘ │
│        ▲                                                             │
│        │ DENY (pod-to-pod)                                           │
│        ▼                                                             │
│  ┌──────────────────┐                                                │
│  │ AI Worker Pod    │  Inbound: DENY ALL                             │
│  │ (YZ analiz)      │  Outbound: S3 read-only, RabbitMQ, PostgreSQL │
│  └──────────────────┘                                                │
│                                                                      │
│  Dosya scratch: /tmp/pipeline/ (Pipeline Pod lokal)                  │
│  Tarama scratch: /tmp/sandbox/ (AV konteyner lokal)                  │
│  Doğrulanmış dosyalar → S3 verified-bucket                           │
│  DB'ye yalnızca EvidenceBundleRef (UUID + S3 path)                   │
└──────────────────────────────────────────────────────────────────────┘
```

**Kritik kurallar:**
- Ingest Gateway ve AI Worker arasında **pod-to-pod ağ trafiği DENY** (KR-070)
- AV2 sandbox konteynerinin **DB bağlantısı yoktur** — yalnızca dosya giriş/çıkış
- Sandbox konteyner ağı kısıtlıdır: yalnızca S3 quarantine-bucket READ
- Dosyalar **asla** Platform Core (Sunucu 1) üzerinden transit etmez (KR-071)
- Quarantine'da kalan dosyalar 7 gün sonra alarm tetikler (ops izleme)

### İki Aşamalı Tarama Zinciri (KR-073)

| Aşama | Konum | Çıktı | Amacı |
|-------|-------|-------|-------|
| AV1 | EdgeKiosk (saha) | `scan_report_edge.json` | Bariz zararlıyı erken yakala |
| AV2 | Sunucu 2 (merkez sandbox) | `scan_report_center.json` | İkinci kontrol + kurcalama ispatı |

Her iki aşamada **hash doğrulama** ve **dosya tipi whitelist** zorunludur (KR-072).

### Tarama Politikası Entegrasyonu (KR-073 scan_policy)

Pipeline Orchestrator, dosya işleme sırasında `scan_policy` parametresine göre
AV2 sandbox'ı koşullu çağırır (detay: SSOT [KR-073]):

```
                              ┌───────────────────────────┐
 S3 quarantine event ────────►│   Pipeline Orchestrator   │
                              │                           │
                              │   scan_policy?            │
                              │    ├── SMART (varsayılan) │
                              │    │   anomali var? ──────┼──► AV2 Sandbox (tam tarama)
                              │    │   anomali yok? ──────┼──► Hash + Whitelist (hafif yol)
                              │    │                      │
                              │    └── BYPASS             │
                              │        hash + whitelist ──┼──► Doğrudan devam
                              │        (72h TTL,          │
                              │         CENTRAL_ADMIN,    │
                              │         il+zaman sınırlı) │
                              │                           │
                              │    MANDATORY (il override) │
                              │        ──────────────────┼──► AV2 Sandbox (zorunlu)
                              └───────────────────────────┘
```

- **SMART** (varsayılan): Koşullu AV2 — anomali yoksa hafif yol (KR-073)
- **BYPASS** (istisna): CENTRAL_ADMIN, coğrafi+zamansal sınırlı, 72h TTL (KR-073)
- **MANDATORY** (il override): Global mod ne olursa olsun tam AV2
- Her modda hash doğrulama + dosya tipi whitelist **asla atlanamaz**
- Mod değişiklikleri `audit_logs` tablosuna yazılır:
  `SCAN_POLICY.CHANGE` / `SCAN_POLICY.BYPASS_ENABLE` / `SCAN_POLICY.BYPASS_EXPIRE`

---

## §7 Dağıtım Yaşam Döngüsü

### Bağımsız Deploy

Sunucu 1 ve Sunucu 2 **bağımsız** deploy edilebilir. Aşağıdaki koşullar sağlandığı
sürece birinin güncellenmesi diğerini **etkilemez**:

| Koşul | Açıklama | KR Ref |
|-------|----------|--------|
| DB şema uyumu | Alembic migration'lar iki taraf için uyumlu | KR-081 |
| Queue mesaj formatı | RabbitMQ mesaj şeması sürümlü (contract-first) | KR-081 |
| S3 bucket yapısı | quarantine/verified bucket adları ve IAM politikaları tutarlı | KR-072 |

### Deploy Sırası (Breaking Change Durumunda)

1. DB migration (her iki sunucuyu da destekleyen "expand" fazı)
2. Sunucu 2 deploy (yeni şemayı okuyabilir)
3. Sunucu 1 deploy (yeni şemayı okuyabilir)
4. DB migration temizlik ("contract" fazı — eski sütun/tablo kaldırma)

---

## §8 Mevsimsel Ölçekleme — Pipeline Profili

### Ölçekleme Profili (Mayıs–Ekim)

Sunucu 2 (Data Pipeline) yükü aktif drone uçuş sezonu ile doğru orantılıdır.
Mayıs–Ekim döneminde pipeline 3–5× horizontal ölçeklenir:

```
       Oca  Şub  Mar  Nis  May  Haz  Tem  Ağu  Eyl  Eki  Kas  Ara
       ─────────────────────────────────────────────────────────────
S2     ░░░  ░░░  ░░░  ░░░  ███  ███  ███  ███  ███  ██░  ░░░  ░░░
(Pipe) düşük           yüksek (drone uçuş + veri toplama sezonu)
       ─────────────────────────────────────────────────────────────
```

| Dönem | Neden | Ölçekleme |
|-------|-------|-----------|
| Mayıs–Ekim (peak) | Aktif drone uçuşları, yoğun veri toplama, AV2 tarama + YZ analiz hacmi | Yeni pipeline instance'ları ile horizontal scale (3–5×) |
| Kasım–Nisan (off) | Uçuş yok veya minimal | Tek instance, minimum kaynak |

### Ölçekleme Stratejisi

Mayıs–Ekim döneminde:
- Ingest Gateway replica sayısı artırılır (paralel manifest işleme)
- AV2 sandbox konteyner sayısı artırılır (paralel tarama)
- AI Worker replica sayısı artırılır (paralel analiz)
- RabbitMQ consumer sayısı orantılı büyütülür
- Ekim sonrası instance'lar geri çekilir (scale-down)

---

## Checklists

### Preflight
- DB role'leri (`platform_core_rw`, `pipeline_rw`) oluşturuldu ve GRANT/REVOKE doğru.
- Ağ politikaları (firewall / K8s NetworkPolicy) §6 matrisine uygun.
- S3 bucket IAM politikaları `data_lifecycle_transfer.md` §6 erişim kontrol matrisine uygun.
- RabbitMQ mesaj şemaları sürümlü ve CI doğrulaması geçiyor (KR-081).
- AV2 sandbox konteyneri DB bağlantısız çalışıyor (izolasyon doğrulaması).
- Ingest Gateway → AI Worker pod-to-pod DENY NetworkPolicy aktif (KR-070).
- Ingest Gateway allowlist IP listesi doğru ve mTLS sertifikaları geçerli.
- `scan_policy` varsayılan değeri SMART olarak konfigüre edilmiş (KR-073).

### Operate
- Sunucu 2 AI Worker inbound bağlantı denemesi izleniyor → alarm (KR-070).
- Ingest Gateway'e allowlist dışı IP denemesi izleniyor → alarm.
- `pipeline_rw` rolünün erişmemesi gereken tablolara sorgu denemesi izleniyor.
- Quarantine-bucket dosya yaşı izleniyor (7+ gün → alarm).
- Mevsimsel ölçekleme geçişleri loglanıyor.
- RabbitMQ queue derinliği izleniyor (backpressure alarm).
- BYPASS modu aktifken dashboard kırmızı banner gösteriliyor.
- BYPASS 72h TTL aşımı → otomatik SMART'a dönüş doğrulanıyor.
- `SCAN_POLICY.CHANGE` / `SCAN_POLICY.BYPASS_ENABLE` audit olayları izleniyor.

### Postmortem
- Sunucu bölme kararının SLA üzerindeki etkisi değerlendirildi.
- Pipeline scale-up/down geçişlerinde veri kaybı olmadığı doğrulandı.
- DB role ayrımının güvenlik ihlali senaryosundaki etkisi test edildi.

## Related docs
- `docs/architecture/data_lifecycle_transfer.md` — Veri akışı ve transfer detayları (kanonik)
- `docs/architecture/clean_architecture.md` — Katman sınırları ve bağımlılık kuralları
- `docs/architecture/event_driven_design.md` — Event tipleri ve idempotency
- `docs/architecture/training_feedback_architecture.md` — YZ eğitim geri bildirim döngüsü
- `docs/architecture/adaptive_rate_limiting.md` — Rate limiting ve mevsimsel profiller
- `config/rate_limits/seasonal_config.yaml` — Mevsimsel rate-limit konfigürasyonu
- `deploy/k8s/deployment.yaml` — K8s dağıtım manifest'i
- `deploy/k8s/network-policy.yaml` — K8s ağ politikaları
- `docs/api/openapi.yaml` — OpenAPI 3.1.0 spesifikasyonu
- `contracts/schemas/edge/` — EdgeKiosk ingest contract şemaları
