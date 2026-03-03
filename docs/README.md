BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.

# Title
Docs Directory Guide (Living Documentation)

## Scope
Bu dosya `docs/` altındaki bilgi mimarisini, güncelleme akışını ve PR doğrulama yaklaşımını tanımlar.

## Owners
- Staff Backend Architect
- Technical Writer
- Platform Owner

## Last updated
2026-03-03

## SSOT references
- KR-000 (doküman seti okuma rehberi)
- KR-015 (pilot kapasite/planlama)
- KR-017 (YZ analiz hattı — şemsiye KR)
- KR-018 / KR-082 (radyometrik kalibrasyon + spektral kapasite algılama)
- KR-033 (ödeme + manuel onay + audit)
- KR-034 (drone tedarik bağımsızlığı)
- KR-050 (kimlik doğrulama)
- KR-063 (roller ve yetkiler — RBAC)
- KR-066 (güvenlik ve KVKK)
- KR-070 (worker isolation & egress policy)
- KR-071 (one-way data flow + allowlist)
- KR-072 (dataset lifecycle + kanıt zinciri)
- KR-073 (untrusted file handling + AV + sandbox)
- KR-081 (contract-first / schema gates)
- KR-084 (termal veri işleme ve sulama stresi)

## How to read this docs set
1. Önce `docs/TARLAANALIZ_SSOT_v1_2_0.txt` okunur (KR Domain İndeksi ile navigasyon).
2. Sonra `docs/views/` ile sistem resmi görülür.
3. `docs/architecture/` ile tasarım kararları doğrulanır.
4. `docs/api/` ile contract seviyesi kontrol edilir.
5. `docs/runbooks/` ile işletim prosedürleri çalıştırılır.
6. `docs/security/` ile risk ve koruma önlemleri doğrulanır.
7. `docs/kr/kr_registry.md` ile KR kayıt defteri kontrol edilir.
8. `docs/governance/` ile yönetişim paketi incelenir.
9. `docs/adr/` ile mimari karar kayıtları (ADR) gözden geçirilir.

### SSOT v1.2.0 Bölüm Yapısı
- **BÖLÜM 1:** Kanonik Kurallar [KR-xxx] — değiştirilemez normatif kurallar.
- **BÖLÜM 2:** Saha Operasyonları (SOP) — pilot, istasyon, Pix4D, QC prosedürleri.
- **BÖLÜM 3:** Gözlemlenebilirlik (Observability) — JSONL log şeması, correlation_id, WORM audit.
- **BÖLÜM 4:** Threat Model One-Pager — varlık/tehdit/kontrol matrisi.
- **BÖLÜM 5:** Güvenlik ve Denetlenebilirlik Navigasyonu — tek bakışta yönlendirme.
- **BÖLÜM 6:** Test Senaryoları — Expert Portal + güvenlik test matrisleri.
- **EK-SOP-SEC:** Saha Güvenlik Checklist (Pilot + İstasyon).

## Documentation classes
- `docs/api/`: API contract, auth, endpoint davranışları.
- `docs/architecture/`: katman, event, scheduler, portal, data lifecycle ve two-server kararları.
- `docs/runbooks/`: operasyon adımları, incident prosedürleri, ödeme onay ve SLA breach akışları.
- `docs/security/`: DDoS mitigasyon ve model koruma stratejileri.
- `docs/views/`: üst-seviye sistem görünümleri (SDLC, 3D Grouping, Capabilities).
- `docs/kr/`: KR kayıt defteri — tüm kuralların indeks ve durum takibi.
- `docs/governance/`: yönetişim paketi (GOVERNANCE_PACK).
- `docs/adr/`: Architecture Decision Records (ADR).
- `docs/migration_guides/`: sürüm geçiş rehberleri.
- `docs/archive/`: arşivlenmiş (superseded) dokümanlar.

## Living docs principles
- Karar metni yerine KR referansı kullanılır.
- SSOT SemVer ile sürümlenir: breaking change → major, geriye uyumlu ekleme → minor, düzeltme → patch (KR-000).
- Contract-first yaklaşımı korunur; şema değişiklikleri CI gate ile doğrulanır (KR-081).
- Operasyonel prosedürler gözlemlenebilir metriklerle ilişkilendirilir; correlation_id uçtan uca taşınır (BÖLÜM 3).
- Kanıt zinciri (chain of custody): manifest/hash/signature doğrulaması zorunludur (KR-072).
- Spektral kapasite algılama: bant sınıfı (BASIC_4BAND / EXTENDED_5BAND / THERMAL) raporlama derinliğini belirler (KR-018/KR-082).
- Doküman değişikliği kod/contract değişikliği ile aynı PR içinde yapılır.

## Docs update flow
- Değişiklik tetikleyicisi: endpoint, şema, runbook, güvenlik kontrolü veya KR kuralı değişimi.
- Etki analizi: ilgili KR ve bağlı dokümanlar listelenir; KR Domain İndeksi referans alınır.
- Güncelleme: dosya başlığı meta alanları + içerik + checklist.
- Doğrulama: örnek istek/yanıt, olay akışı, observability alanları, correlation_id propagation.

## PR checklist (docs)
- İlgili KR referansları eklendi mi?
- API adları `docs/api/openapi.yaml` ile tutarlı mı?
- PII redaction örnekleri maskeli mi? (KR-066)
- Runbook adımları rollback/postmortem içeriyor mu?
- Related docs listesi güncellendi mi?
- Güvenlik kuralları (KR-070–073) ile tutarlılık doğrulandı mı?
- Observability alanları (correlation_id, audit olay adları) BÖLÜM 3 ile uyumlu mu?
- Spektral/termal pipeline değişiklikleri KR-018/KR-082 ve KR-084 ile tutarlı mı?
- Threat model (BÖLÜM 4) etkileniyorsa güncellendi mi?
- `docs/kr/kr_registry.md` güncel mi?

## Checklists
### Preflight
- SSOT sürümü (v1.2.0) doğrulandı.
- Etkilenen dosyalar haritalandı.
- Terminoloji tutarlılığı kontrol edildi.
- KR Domain İndeksi ile ilgili paket (A–E) belirlendi.

### Operate
- Değişiklik sonrası endpoint/şema örnekleri doğrulandı.
- Runbook ve security doküman bağlantıları doğrulandı.
- Observability: correlation_id akışı ve WORM audit olayları kontrol edildi.
- Saha güvenlik checklist (EK-SOP-SEC) ile tutarlılık doğrulandı.

### Postmortem
- Yanlış veya eksik kural referansı varsa düzeltildi.
- Gelecek güncelleme için açık aksiyonlar kaydedildi.
- Threat model (BÖLÜM 4) değişiklik gerektiriyorsa güncellenmiş mi kontrol edildi.

## Related docs
- `docs/TARLAANALIZ_SSOT_v1_2_0.txt`
- `docs/api/openapi.yaml`
- `docs/views/VIEW_SDLC.md`
- `docs/kr/kr_registry.md`
- `docs/governance/GOVERNANCE_PACK_v1_0_0.md`
- `docs/adr/ADR-001-nine-state-machine.md`
- `docs/architecture/data_lifecycle_transfer.md`
- `docs/security/model_protection_strategy.md`
