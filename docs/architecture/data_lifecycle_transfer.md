BOUND: TARLAANALIZ_SSOT_v1_0_0.txt – canonical rules are referenced, not duplicated.

# Title
Data Lifecycle & Transfer Architecture

## Scope
Veri yaşam döngüsü, M2 (EdgeKiosk)–Ingest Gateway–Worker arası transfer stratejisi, nesne depolama mimarisi ve ağ akış kurallarını tanımlar.

## Owners
- Staff Backend Architect
- Security Lead
- Integration Lead

## Last updated
2026-03-01

## SSOT references
- KR-070 (Worker Isolation)
- KR-071 (One-way Data Flow)
- KR-072 (Dataset Lifecycle + Chain of Custody)
- KR-073 (Untrusted File Handling + AV1/AV2)
- KR-081 (Contract-First)
- KR-030 (Drone Registry)

---

## §1 Mimari Karar

Platform artık M2 (EdgeKiosk) cihazından büyük veri aktarımı **ALMAZ**. Bunun yerine:

1. M2 (EdgeKiosk) **manifest JSON + meta veri** gönderir (`POST /edge/ingest`)
   Hedef: **Sunucu 2 — Ingest Gateway** (ayrı pod, M2 allowlist IP + mTLS)
2. Ingest Gateway manifesti doğrular ve **ön-imzalı (presigned) S3 yükleme URL'leri** döner
3. M2 dosyaları **doğrudan S3 quarantine-bucket'a** yazar (HTTP PUT)

> **Not:** Ingest Gateway, Sunucu 2 (Data Pipeline) üzerinde **ayrı pod** olarak çalışır.
> AI Worker ile **pod-to-pod ağ trafiği DENY** (KR-070). Bkz. `two_server_architecture.md` §3.

Bu mimari ile Platform Core (Sunucu 1) hiçbir zaman büyük ikili (binary) veri taşımaz
ve saha cihazı trafiğine maruz kalmaz; yalnızca küçük JSON meta veri ve orkestrasyon
mesajları ile çalışır.

---

## §2 Dataset Durum Makinesi

Dataset birinci sınıf domain nesnesidir (KR-072). Kanonik durumlar:

```
RAW_INGESTED ──► RAW_SCANNED_EDGE_OK ──► RAW_HASH_SEALED
                                              │
                                              ▼
                                          CALIBRATED
                                              │
                                              ▼
                                 CALIBRATED_SCANNED_CENTER_OK
                                              │
                                              ▼
                                    DISPATCHED_TO_WORKER
                                              │
                                              ▼
                                          ANALYZED
                                              │
                                              ▼
                                      DERIVED_PUBLISHED
                                              │
                                              ▼
                                          ARCHIVED

  ── herhangi bir aşamada hata/şüphe ──► REJECTED_QUARANTINE
```

Her durum geçişi event/audit ile ispatlanır. Geri dönüş yoktur; hata durumunda
dataset `REJECTED_QUARANTINE`'a alınır ve yeni ingest gerekir.

---

## §3 Uçtan Uca Veri Akışı

```
┌──────────┐  manifest JSON   ┌──────────────┐  presigned URLs  ┌──────────┐
│          │  + meta veri      │ Sunucu 2      │  (yanıt)         │          │
│ M2       ├──────────────────►│ Ingest Gateway├─────────────────►│ M2       │
│(EdgeKiosk│  POST /ingest     │ (ayrı pod)    │  200 OK          │(EdgeKiosk│
└────┬─────┘  mTLS+allowlist   └──────┬────────┘                  └────┬─────┘
     │                               │                            │
     │  HTTP PUT (presigned URL)     │  job dispatch              │
     │  ham görüntü dosyaları        │  (RabbitMQ)                │
     ▼                               ▼                            │
┌──────────────────┐          ┌──────────┐                        │
│  S3 quarantine   │          │ RabbitMQ │                        │
│  bucket          │          │ (queue)  │                        │
│  (karantina)     │          └─────┬────┘                        │
└────────┬─────────┘                │                             │
         │                          │  pull/poll                  │
         │  AV2 + hash verify       │                             │
         ▼                          ▼                             │
┌──────────────────┐          ┌──────────┐                        │
│  S3 verified     │◄─────────│  Worker  │                        │
│  bucket          │  read    │ (YZ)     │                        │
│  (doğrulanmış)   │  only    └─────┬────┘                        │
└──────────────────┘                │                             │
                                    │  AnalysisResult             │
                                    ▼                             │
                             ┌──────────┐                         │
                             │ Platform │  sonuç                  │
                             │ (results)├────────► Web/PWA        │
                             └──────────┘                         │
```

**Akış özeti (KR-071 kanonik sıra):**
1. **M2 (EdgeKiosk) → Sunucu 2 Ingest Gateway:** mTLS + allowlist IP + manifest JSON (< 1 KB)
2. **Ingest Gateway → M2:** Presigned URL listesi (< 1 KB)
3. **M2 → S3 quarantine-bucket:** Ham dosyalar (HTTP PUT, ~1 TB, 1 kez)
4. **Sunucu 2 Pipeline:** AV2 tarama + SHA-256 hash doğrulama → quarantine → verified
5. **Sunucu 1 Platform → RabbitMQ:** Job dispatch bildirimi (< 1 KB)
6. **Worker ← Queue:** Pull/poll ile iş alma
7. **Worker ← S3 verified-bucket:** Dataset okuma (read-only, 1 kez)
8. **Worker → DB:** Sonuç doğrudan `analysis_jobs` tablosuna yazılır (CQRS)
9. **Web/PWA ← Sunucu 1 Platform:** Sadece sonuç okur; ham veri yok

---

## §4 Tek Yönlü Ağ Akışları

### POST /edge/ingest — İngest Akışı

M2 (EdgeKiosk), manifest JSON ve meta veriyi **Sunucu 2 üzerindeki Ingest Gateway**'e
gönderir (mTLS + allowlist IP). Ingest Gateway manifesti doğrular (SHA-256 hash kontrolü,
drone_id uyumu, sertifika doğrulama) ve her dosya için ön-imzalı S3 yükleme URL'si döner.
M2 bu URL'lerle dosyaları **doğrudan S3 quarantine-bucket'a** yazar.

```
M2 (EdgeKiosk)                 Ingest Gateway (Sunucu 2)      S3
   │                              │                            │
   │  POST /edge/ingest          │                            │
   │  Content-Type: app/json     │                            │
   │  Body: {manifest, meta}     │                            │
   │  mTLS + allowlist IP        │                            │
   │─────────────────────────────►│                            │
   │                              │                            │
   │                              │  1. manifest hash doğrula  │
   │                              │  2. drone_id → registry    │
   │                              │  3. presigned URL üret     │
   │                              │                            │
   │  200 OK                      │                            │
   │  {upload_urls, session_id,   │                            │
   │   quarantine_bucket,         │                            │
   │   max_file_size_bytes}       │                            │
   │◄─────────────────────────────│                            │
   │                              │                            │
   │  HTTP PUT (presigned URL)    │                            │
   │  dosya-1.tif                 │                            │
   │──────────────────────────────┼───────────────────────────►│
   │  HTTP PUT (presigned URL)    │                            │
   │  dosya-2.tif                 │                            │
   │──────────────────────────────┼───────────────────────────►│
   │  ...                         │                            │
   │                              │                            │
   │                              │  S3 Event Notification     │
   │                              │◄───────────────────────────│
   │                              │                            │
   │                              │  AV2 + hash verify başlat  │
   │                              │                            │
```

**Kritik kurallar:**
- Ingest Gateway büyük dosya **almaz** ve **iletmez** — yalnızca presigned URL üretir
- M2 dosyaları Ingest Gateway'e **göndermez** — doğrudan S3'e yazar
- Hash uyuşmazlığı → `REJECTED_QUARANTINE` + audit event (KR-072)
- Kayıtsız drone_id → talep reddedilir (KR-030)

### Diğer Akışlar

- **Sunucu 1 → Queue (dispatch):** Job bildirimi; Worker pull ile alır (KR-070)
- **Worker → S3 verified-bucket:** Read-only erişim; mTLS + kısa ömürlü token (KR-070)
- **Worker → DB (sonuç):** Türev sonuç doğrudan `analysis_jobs` tablosuna yazılır; Sunucu 1 CQRS ile okur
- **Web/PWA → Sunucu 1:** Sadece sonuç okur; ham veriye erişim yok

---

## §5 Kanonik API

### POST /edge/ingest (Sunucu 2 — Ingest Gateway)

**Request**

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `manifest` | object | Evet | IntakeManifest (KR-072). `$ref: intake_manifest.v1.schema.json` |
| `file_count` | integer | Evet | Yüklenecek dosya sayısı (min: 1) |
| `total_size_bytes` | integer | Evet | Toplam boyut, byte (min: 1) |
| `drone_id` | string | Evet | Drone kayıt ID (KR-030 uyumu) |
| `flight_session_id` | string (UUID) | Evet | Uçuş oturumu ID |
| `captured_at` | string (ISO 8601) | Evet | Görüntü çekim zamanı (UTC) |
| `sha256_manifest_hash` | string (hex64) | Evet | Manifest SHA-256 hash (KR-072) |

Content-Type: `application/json` — dosya yok, yalnızca manifest + meta veri.

Contract şeması: `contracts/schemas/edge/dataset_ingest_request.v1.schema.json`

**Response (200 OK)**

| Alan | Tip | Açıklama |
|------|-----|----------|
| `upload_urls` | array | Her dosya için presigned URL nesnesi |
| `upload_urls[].filename` | string | Dosya adı (manifest ile eşleşir) |
| `upload_urls[].presigned_url` | string (URI) | S3 presigned PUT URL |
| `upload_urls[].expires_in_seconds` | integer | URL geçerlilik süresi (sn) |
| `session_id` | string (UUID) | İngest oturumu ID |
| `quarantine_bucket` | string | S3 karantina bucket adı |
| `max_file_size_bytes` | integer | Tek dosya maks. boyut (byte) |

Contract şeması: `contracts/schemas/edge/dataset_ingest_response.v1.schema.json`

**Hata Durumları**

| HTTP | Durum | Açıklama |
|------|-------|----------|
| 400 | `MANIFEST_HASH_MISMATCH` | sha256_manifest_hash doğrulama başarısız |
| 400 | `INVALID_DRONE_ID` | drone_id kayıt defterinde yok (KR-030) |
| 400 | `SCHEMA_VALIDATION_ERROR` | JSON Schema doğrulama hatası (KR-081) |
| 401 | `MTLS_AUTH_FAILED` | mTLS sertifika doğrulama başarısız |
| 413 | `PAYLOAD_TOO_LARGE` | total_size_bytes platform limitini aşıyor |
| 429 | `RATE_LIMIT_EXCEEDED` | İstek hız limiti aşıldı |

---

## §6 Nesne Depolama Stratejisi

### İki Kova Mimarisi

```
                    ┌─────────────────────────────────┐
                    │         S3 Object Storage        │
                    │                                  │
  EdgeKiosk ──PUT──►│  ┌─────────────────────┐        │
  (presigned URL)   │  │  quarantine-bucket   │        │
                    │  │  (karantina kovası)   │        │
                    │  │                       │        │
                    │  │  ● Ham dosyalar       │        │
                    │  │  ● Henüz doğrulanmamış│        │
                    │  │  ● EdgeKiosk YAZMA    │        │
                    │  │  ● Platform OKUMA     │        │
                    │  │  ● Worker ERİŞİM YOK  │        │
                    │  └──────────┬────────────┘        │
                    │             │                     │
                    │      AV2 tarama PASS              │
                    │      SHA-256 hash PASS             │
                    │      Kalibrasyon PASS (KR-018)    │
                    │             │                     │
                    │             ▼                     │
                    │  ┌─────────────────────┐         │
                    │  │  verified-bucket     │         │
                    │  │  (doğrulanmış kova)  │         │
                    │  │                      │         │
                    │  │  ● Doğrulanmış veri  │         │
                    │  │  ● EdgeKiosk ERİŞİM  │         │
                    │  │    YOK               │         │
                    │  │  ● Platform TAŞIMA   │         │
                    │  │  ● Worker OKUMA      │         │
                    │  └─────────────────────┘         │
                    └─────────────────────────────────┘
```

### Erişim Kontrol Matrisi

| Aktör | quarantine-bucket | verified-bucket |
|-------|-------------------|-----------------|
| M2 (EdgeKiosk) | **WRITE** (presigned URL ile) | **DENY** |
| Sunucu 2 Pipeline | **READ** (AV2 + hash doğrulama) | **WRITE** (taşıma) |
| Worker | **DENY** | **READ** (mTLS + kısa ömürlü token) |
| Web/PWA | **DENY** | **DENY** |

### Doğrulama Süreci

1. EdgeKiosk presigned URL ile dosyaları quarantine-bucket'a yazar
2. S3 Event Notification ile Platform bilgilendirilir
3. Platform quarantine-bucket üzerinde şu kontrolleri yapar:
   - **AV2 tarama** (merkez antivirüs): `scan_report_center.json` üretilir (KR-073)
   - **SHA-256 hash doğrulama**: Manifest'teki hash'ler ile S3 nesneleri karşılaştırılır (KR-072)
   - **Kalibrasyon kontrolü**: `requires_calibrated=true` → kalibrasyon kanıtı aranır (KR-018)
4. Tüm kontroller **PASS** → dosyalar verified-bucket'a taşınır
5. Herhangi bir kontrol **FAIL** → dataset `REJECTED_QUARANTINE` + audit event

### Güvenlik Garantileri

- **Zararlı dosya asla verified-bucket'a geçemez:** AV2 FAIL → quarantine kalır
- **Kurcalanmış dosya asla verified-bucket'a geçemez:** Hash mismatch → quarantine kalır
- **Worker asla ham/doğrulanmamış veri okumaz:** quarantine-bucket'a erişim yok (KR-070)
- **EdgeKiosk asla doğrulanmış veriye erişemez:** verified-bucket'a erişim yok

---

## §7 Transfer Matrisi

Platform hiçbir zaman büyük veri taşımaz. Aşağıdaki tablo uçtan uca transfer
boyutlarını ve yönlerini özetler:

| Transfer | Boyut | Kaynak → Hedef | Protokol | Sıklık |
|----------|-------|----------------|----------|--------|
| Manifest JSON + meta veri | < 1 KB | M2 (EdgeKiosk) → Ingest Gateway (Sunucu 2) | HTTPS (mTLS + allowlist) | Her ingest |
| Presigned URL yanıtı | < 1 KB | Ingest Gateway → M2 | HTTPS | Her ingest |
| Ham görüntü dosyaları | ~1 TB | EdgeKiosk → S3 quarantine | HTTPS (presigned PUT) | 1 kez |
| Doğrulanmış dosya taşıma | ~1 TB | S3 quarantine → S3 verified | S3 internal (COPY) | 1 kez |
| İş bildirimi (dispatch) | < 1 KB | Platform → RabbitMQ | AMQP | Her job |
| Dataset indirme (analiz) | ~1 TB | S3 verified → Worker | HTTPS (mTLS) | 1 kez |
| Analiz sonucu | < 10 MB | Worker → Platform | HTTPS (mTLS) | Her job |
| Sonuç görüntüleme | < 1 MB | Platform → Web/PWA | HTTPS | Her istek |

**Kritik gözlem:** Platform Core (Sunucu 1) API sunucusu üzerinden büyük veri geçmez.
Ingest Gateway yalnızca manifest JSON (<1 KB) işler. ~1 TB büyüklüğündeki ham görüntü
verileri ne Sunucu 1'i ne de Ingest Gateway'i transit etmez; M2 ve Worker doğrudan
S3 ile iletişim kurar.

---

## Checklists

### Preflight
- Contract şemaları güncel ve CI doğrulaması geçiyor (KR-081).
- S3 bucket IAM politikaları erişim kontrol matrisiyle uyumlu.
- Presigned URL TTL değeri konfigürasyonda tanımlı.
- AV2 tarama motoru güncel imza veritabanı ile çalışıyor.

### Operate
- Quarantine-bucket dosya yaşı izleniyor (7+ gün → alarm).
- Hash doğrulama başarısızlık oranı izleniyor.
- Presigned URL süre aşımı oranı izleniyor.
- S3 quarantine → verified taşıma süresi izleniyor.

### Postmortem
- Hash mismatch veya AV fail kök neden analizi tamamlandı.
- Quarantine'da takılan dataset'ler için düzeltme aksiyonu alındı.
- Transfer matrisi boyut tahminleri gerçek verilerle güncellendi.

## Related docs
- `contracts/schemas/edge/dataset_ingest_request.v1.schema.json`
- `contracts/schemas/edge/dataset_ingest_response.v1.schema.json`
- `contracts/schemas/edge/intake_manifest.v1.schema.json`
- `docs/architecture/clean_architecture.md`
- `docs/architecture/event_driven_design.md`
- `docs/api/openapi.yaml`
- `docs/runbooks/incident_response_payment_timeout.md`
