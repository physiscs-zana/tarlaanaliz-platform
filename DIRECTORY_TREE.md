# TarlaAnaliz Platform — Dizin Yapısı (Tree)

> **Bu dosyanın konumu:** `tarlaanaliz-platform_/DIRECTORY_TREE.md`
> **Son güncelleme:** 2026-03-08

```
tarlaanaliz-platform/
├── .dockerignore                (Docker build dışı dosya listesi)
├── .env.example                 (Ortam değişkenleri şablonu; → settings.py)
├── .gitattributes               (Git dosya öznitelikleri)
├── .gitignore                   (Git izleme dışı dosya listesi)
├── .gitmodules                  (Git submodule tanımları; → contracts/)
├── .pre-commit-config.yaml      (Pre-commit hook tanımları; ruff, mypy)
├── AGENTS.md                    (Claude Code agent talimatları)
├── CHANGELOG.md                 (Sürüm değişiklik günlüğü)
├── CONTRACTS_SHA256.txt         (Contract şema hash doğrulama; → contracts/)
├── CONTRACTS_VERSION.md         (Contract sürüm bilgisi; → contracts/)
├── DEEP_AUDIT_REPORT_v2.md     (Derin denetim raporu)
├── DIRECTORY_TREE.md            ← bu dosya
├── Dockerfile                   (Docker imaj tanımı; → pyproject.toml, src/)
├── MANIFEST_CANONICAL.md        (Kanonik dosya manifest listesi)
├── PRODUCTION_READINESS_REPORT.md (Üretime hazırlık raporu)
├── README.md                    (Proje tanıtım ve kurulum rehberi)
├── SSOT_COMPATIBILITY_AUDIT_REPORT.md (SSOT uyumluluk denetim raporu)
├── alembic.ini                  (Alembic DB migration ayarları; → alembic/)
├── docker-compose.yml           (Docker Compose servis tanımları)
├── pyproject.toml               (Python proje ayarları; ruff, mypy, pytest, bağımlılıklar)
│
├── .github/
│   ├── pull_request_template.md (PR şablonu)
│   └── workflows/
│       ├── ci.yml               (CI pipeline: lint, mypy, pytest, SSOT compliance)
│       ├── contract_validation.yml (Contract şema doğrulama CI)
│       ├── deploy-staging.yml   (Staging ortamı deploy pipeline)
│       ├── frontend-ci.yml      (Frontend lint, test, build CI)
│       └── security.yml         (Güvenlik tarama CI; trivy, bandit)
│
├── alembic/
│   ├── env.py                   (Alembic ortam ayarları; → database.py)
│   ├── script.py.mako           (Migration dosya şablonu)
│   └── versions/
│       ├── 20260101_001_initial_users_roles.py       (Kullanıcı ve rol tabloları)
│       ├── 20260101_002_initial_fields_crops.py      (Tarla ve bitki tabloları)
│       ├── 20260101_003_initial_missions.py          (Görev tabloları)
│       ├── 20260102_004_subscriptions.py             (Abonelik tabloları)
│       ├── 20260102_005_pilots.py                    (Pilot tabloları)
│       ├── 20260102_006_experts.py                   (Uzman tabloları)
│       ├── 20260103_007_analysis_jobs.py             (Analiz iş tabloları)
│       ├── 20260103_008_expert_reviews.py            (Uzman inceleme tabloları)
│       ├── 20260104_009_weather_blocks.py            (Hava engeli tabloları)
│       ├── 20260104_010_audit_logs.py                (Denetim günlüğü tabloları)
│       ├── 20260104_011_weekly_schedules.py          (Haftalık planlama tabloları)
│       ├── 20260105_012_indexes_performance.py       (Performans indeksleri)
│       ├── 20260105_013_full_text_search.py          (Tam metin arama indeksleri)
│       ├── 20260129_kr033_payment_intents.py         (KR-033 ödeme intent tabloları)
│       ├── 20260201_kr082_calibration_qc_records.py  (KR-082 kalibrasyon/QC tabloları)
│       ├── 20260204_add_weather_block_reports.py     (Hava engeli rapor tabloları)
│       ├── 20260223_kr015c_mission_schedule_fields.py (KR-015 görev takvim alanları)
│       ├── 20260225_014_kr015_mission_segments.py    (KR-015 görev segment tabloları)
│       ├── 20260225_015_kr015_seasonal_reschedule_tokens.py (KR-015-5 reschedule token)
│       ├── 20260302_add_billing_admin_role.py        (BILLING_ADMIN rol ekleme)
│       └── 20260302_simplify_weather_block_status.py (Hava engeli durum sadeleştirme)
│
├── config/
│   ├── drone_capability_matrix.yaml (Drone model-sensor yetenek matrisi; → drone_model.py)
│   ├── drone_registry.yaml      (Onaylı drone kayıt listesi; → drone_registry_loader.py)
│   ├── logging.yaml             (Yapısal loglama ayarları; structlog)
│   └── rate_limits/
│       ├── base_limits.yaml     (Temel rate limit kuralları; → rate_limit_middleware.py)
│       └── seasonal_config.yaml (Sezonsal rate limit ayarları)
│
├── contracts/                   (git submodule — contract-first şema deposu)
│   ├── .gitignore
│   ├── CHANGELOG.md             (Contract sürüm değişiklikleri)
│   ├── CLAUDE.md                (Contract repo agent talimatları)
│   ├── CONTRACTS_VERSION.md     (Aktif contract sürümü)
│   ├── LICENSE
│   ├── PATCH_NOTES.md           (Yama notları)
│   ├── README.md                (Contract repo kullanım rehberi)
│   ├── drone_capability_matrix.yaml (Drone yetenek matrisi kanonik kaynak)
│   ├── drone_registry.yaml      (Drone kayıt kanonik kaynak)
│   ├── package.json             (Node.js bağımlılıkları; TS tip üretimi)
│   ├── pyproject.toml           (Python bağımlılıkları; şema doğrulama)
│   ├── requirements-dev.txt     (Geliştirme bağımlılıkları)
│   ├── update-contracts.ps1     (Contract güncelleme PowerShell scripti)
│   ├── .github/
│   │   └── workflows/
│   │       ├── auto_sync.yml    (Otomatik repo senkronizasyon CI)
│   │       └── contract_validation.yml (Şema doğrulama CI)
│   ├── api/
│   │   ├── edge_local.v1.yaml   (Edge kiosk API OpenAPI tanımı)
│   │   ├── platform_internal.v1.yaml (Platform dahili API OpenAPI)
│   │   ├── platform_public.v1.yaml (Platform halka açık API OpenAPI)
│   │   └── components/
│   │       ├── parameters.yaml  (Ortak API parametreleri)
│   │       ├── responses.yaml   (Ortak API yanıtları)
│   │       ├── schemas.yaml     (Ortak API şemaları)
│   │       └── security_schemes.yaml (Güvenlik şemaları; JWT, mTLS)
│   ├── docs/
│   │   ├── README.md
│   │   ├── TARLAANALIZ_SSOT_v1_2_0.txt (SSOT kanonik kurallar belgesi)
│   │   ├── versioning_policy.md (Şema versiyonlama politikası)
│   │   ├── canonical/
│   │   │   ├── GELISTIRICI_UYGULAMA_PAKETI_v2_4_.docx (Geliştirici uygulama rehberi)
│   │   │   ├── KANONIK_URUN_ISLEYIS_REHBERI_v2_4_.docx (Ürün işleyiş rehberi)
│   │   │   ├── README.md
│   │   │   └── SAHA_OPERASYON_SOP_v2_4_.docx (Saha operasyon prosedürleri)
│   │   ├── checklists/
│   │   │   └── SDLC_GATES.md   (SDLC geçit kontrol listesi)
│   │   ├── examples/
│   │   │   ├── README.md
│   │   │   ├── analysis_job.example.json (Analiz iş örneği)
│   │   │   ├── analysis_result.example.json (Analiz sonuç örneği)
│   │   │   ├── dataset.example.json (Dataset örneği)
│   │   │   ├── dataset_manifest.example.json (Dataset manifest örneği)
│   │   │   ├── field.example.json (Tarla örneği)
│   │   │   ├── intake_manifest.example.json (Alım manifest örneği)
│   │   │   ├── mission.example.json (Görev örneği)
│   │   │   ├── payment_intent_creditcard_paid.example.json (Kredi kartı ödeme örneği)
│   │   │   ├── payment_intent_iban_paid.example.json (IBAN ödeme onaylanmış örneği)
│   │   │   ├── payment_intent_iban_pending.example.json (IBAN ödeme bekleyen örneği)
│   │   │   └── thermal_analysis_result.example.json (Termal analiz sonuç örneği)
│   │   └── migration_guides/
│   │       ├── MIGRATION_GUIDE_TEMPLATE.md (Migrasyon rehber şablonu)
│   │       ├── README.md
│   │       ├── field_v1_to_v2.md (Field şema v1→v2 geçiş rehberi)
│   │       └── payment_intent_v1_to_v2.md (PaymentIntent v1→v2 geçiş rehberi)
│   ├── enums/
│   │   ├── analysis_type.enum.v1.json (Analiz tipi enum değerleri)
│   │   ├── crop_type.enum.v1.json (Bitki tipi enum değerleri)
│   │   ├── dataset_status.enum.v1.json (Dataset durum enum değerleri)
│   │   ├── drone_type.enum.v1.json (Drone tipi enum değerleri)
│   │   ├── mission_status.enum.v1.json (Görev durum enum değerleri)
│   │   ├── payment_method.enum.v1.json (Ödeme yöntemi enum değerleri)
│   │   ├── payment_status.enum.v1.json (Ödeme durumu v1 enum)
│   │   ├── payment_status.enum.v2.json (Ödeme durumu v2 enum)
│   │   ├── payment_target_type.enum.v1.json (Ödeme hedef tipi enum)
│   │   ├── qc_status.enum.v1.json (QC durumu enum değerleri)
│   │   ├── quarantine_decision.enum.v1.json (Karantina kararı enum)
│   │   ├── role.enum.v1.json    (Rol enum değerleri; 13 rol)
│   │   ├── scan_stage.enum.v1.json (Tarama aşaması enum)
│   │   ├── threat_type.enum.v1.json (Tehdit tipi enum)
│   │   ├── user_role.enum.v1.json (Kullanıcı rol enum)
│   │   └── verification_status.enum.v1.json (Doğrulama durumu enum)
│   ├── schemas/
│   │   ├── core/
│   │   │   ├── field.v1.schema.json (Tarla JSON Schema)
│   │   │   ├── mission.v1.schema.json (Görev JSON Schema)
│   │   │   ├── user.v1.schema.json (Kullanıcı JSON Schema)
│   │   │   └── user_pii.v1.schema.json (Kullanıcı PII JSON Schema)
│   │   ├── datasets/
│   │   │   ├── attestation.v1.schema.json (Onay belgesi şeması)
│   │   │   ├── calibration_certificate.v1.schema.json (Kalibrasyon sertifikası)
│   │   │   ├── dataset.v1.schema.json (Dataset şeması)
│   │   │   ├── dataset_manifest.v1.schema.json (Dataset manifest şeması)
│   │   │   ├── evidence_bundle_ref.v1.schema.json (Kanıt paketi referansı)
│   │   │   ├── qc_report.v1.schema.json (QC raporu şeması)
│   │   │   ├── scan_report.v1.schema.json (Tarama raporu şeması)
│   │   │   ├── transfer_batch.v1.schema.json (Transfer partisi şeması)
│   │   │   └── verification_report.v1.schema.json (Doğrulama raporu şeması)
│   │   ├── edge/
│   │   │   ├── calibration_result.v1.schema.json (Edge kalibrasyon sonucu)
│   │   │   ├── dataset_manifest.v1.schema.json (Edge dataset manifest)
│   │   │   ├── edge_metadata.v1.schema.json (Edge metadata)
│   │   │   ├── intake_manifest.v1.schema.json (Alım manifest şeması)
│   │   │   ├── qc_report.v1.schema.json (Edge QC raporu)
│   │   │   ├── quarantine_event.v1.schema.json (Karantina olay şeması)
│   │   │   ├── scan_report.v1.schema.json (Edge tarama raporu)
│   │   │   ├── transfer_batch.v1.schema.json (Edge transfer partisi)
│   │   │   └── verification_report.v1.schema.json (Edge doğrulama raporu)
│   │   ├── events/
│   │   │   ├── analysis_completed.v1.schema.json (Analiz tamamlandı event)
│   │   │   ├── dataset_analyzed.v1.schema.json (Dataset analiz edildi event)
│   │   │   ├── dataset_calibrated.v1.schema.json (Dataset kalibre edildi event)
│   │   │   ├── dataset_dispatched.v1.schema.json (Dataset gönderildi event)
│   │   │   ├── dataset_ingested.v1.schema.json (Dataset alındı event)
│   │   │   ├── dataset_scanned.v1.schema.json (Dataset tarandı event)
│   │   │   ├── dataset_verified.v1.schema.json (Dataset doğrulandı event)
│   │   │   ├── derived_published.v1.schema.json (Türev yayınlandı event)
│   │   │   ├── field_created.v1.schema.json (Tarla oluşturuldu event)
│   │   │   └── mission_assigned.v1.schema.json (Görev atandı event)
│   │   ├── platform/
│   │   │   ├── calibrated_dataset_manifest.v1.schema.json (Kalibre dataset manifest)
│   │   │   ├── calibration_result.v1.schema.json (Kalibrasyon sonucu)
│   │   │   ├── evidence_bundle_ref.v1.schema.json (Kanıt paketi referansı)
│   │   │   ├── layer_registry.v1.schema.json (Katman kayıt şeması)
│   │   │   ├── payment_intent.v1.schema.json (Ödeme intent v1)
│   │   │   ├── payment_intent.v2.schema.json (Ödeme intent v2)
│   │   │   ├── payroll.v1.schema.json (Pilot hakediş şeması)
│   │   │   ├── pricing.v1.schema.json (Fiyatlama şeması)
│   │   │   ├── qc_report.v1.schema.json (Platform QC raporu)
│   │   │   ├── subscription.v1.schema.json (Abonelik şeması)
│   │   │   └── training_feedback.v1.schema.json (Eğitim geri bildirim şeması)
│   │   ├── shared/
│   │   │   ├── address.v1.schema.json (Adres şeması)
│   │   │   ├── geojson.v1.schema.json (GeoJSON şeması)
│   │   │   └── money.v1.schema.json (Para birimi şeması)
│   │   └── worker/
│   │       ├── analysis_job.v1.schema.json (Analiz iş şeması)
│   │       ├── analysis_result.v1.schema.json (Analiz sonuç şeması)
│   │       └── thermal_analysis_result.v1.schema.json (Termal analiz sonuç şeması)
│   ├── ssot/
│   │   ├── GOVERNANCE_PACK_v1_0_1.md (Yönetişim paketi)
│   │   ├── README.md
│   │   ├── contracts_ssot.md    (Contract SSOT eşleme tablosu)
│   │   └── kr_registry.md      (KR kayıt defteri — tüm kurallar)
│   ├── tests/
│   │   ├── test_examples_match_schemas.py (Örnek dosya-şema uyum testi)
│   │   ├── test_no_breaking_changes.py (Geriye uyumluluk testi)
│   │   └── test_validate_all_schemas.py (Tüm şema doğrulama testi)
│   └── tools/
│       ├── breaking_change_detector.py (Kırıcı değişiklik algılama)
│       ├── compute_contracts_sha256.py (Contract SHA-256 hesaplama)
│       ├── generate_types.sh    (TypeScript tip üretme scripti)
│       ├── pin_version.py       (Sürüm sabitleme aracı)
│       ├── read_contracts_version.py (Contract sürüm okuma)
│       ├── sync_to_repos.py     (Repo senkronizasyon Python)
│       ├── sync_to_repos.sh     (Repo senkronizasyon Bash)
│       ├── validate.py          (Şema doğrulama aracı)
│       └── verify_contracts_datasets_layer.py (Dataset katman doğrulama)
│
├── docs/
│   ├── README.md                (Dokümantasyon dizini rehberi)
│   ├── TARLAANALIZ_SSOT_v1_2_0.txt (SSOT kanonik kurallar — ana kaynak)
│   ├── adr/
│   │   └── ADR-001-nine-state-machine.md (KR-072 dokuz-durum makinesi kararı)
│   ├── api/
│   │   ├── authentication.md    (Kimlik doğrulama rehberi; JWT, mTLS)
│   │   └── openapi.yaml         (Platform OpenAPI şeması)
│   ├── architecture/
│   │   ├── adaptive_rate_limiting.md (Uyarlanabilir rate limiting tasarımı)
│   │   ├── clean_architecture.md (Clean Architecture 4-katman tasarımı)
│   │   ├── data_lifecycle_transfer.md (Veri yaşam döngüsü aktarım tasarımı)
│   │   ├── event_driven_design.md (Olay güdümlü mimari tasarımı)
│   │   ├── expert_portal_design.md (Uzman portal tasarımı; KR-019)
│   │   ├── subscription_scheduler_design.md (Abonelik zamanlayıcı tasarımı)
│   │   ├── training_feedback_architecture.md (Eğitim geri bildirim mimarisi)
│   │   └── two_server_architecture.md (İki sunucu mimarisi; platform + edge)
│   ├── archive/
│   │   └── 2026-02/
│   │       ├── GOVERNANCE_PACK_v1_0_0_2026-02-15.md (Eski yönetişim paketi)
│   │       ├── IS_PLANI_AKIS_DOKUMANI_v1_0_0_OLD.docx (Eski iş planı)
│   │       ├── IS_PLANI_AKIS_DOKUMANI_v1_0_0_UPDATED_2026-02-14.docx (Güncel iş planı)
│   │       ├── KR-033_payment_flow_OLD.md (Eski ödeme akışı)
│   │       ├── TARLAANALIZ_LLM_BRIEF_v1_0_0_OLD.md (Eski LLM brief)
│   │       ├── TARLAANALIZ_PLAYBOOK_v1_0_0_OLD.md (Eski playbook)
│   │       ├── TARLAANALIZ_SSOT_v1_0_0_DOCS_CLEAN_2026-02-14_v7.txt (Eski SSOT temiz)
│   │       ├── TARLAANALIZ_SSOT_v1_0_0_OLD.txt (Eski SSOT)
│   │       ├── kr_registry_OPTIMAL_2026-02-14_v7.md (Eski KR kayıt)
│   │       └── tarlaanaliz_platform_tree_v3.2.2_FINAL_2026-02-08_OLD.txt (Eski ağaç)
│   ├── governance/
│   │   └── GOVERNANCE_PACK_v1_0_0.md (Yönetişim paketi; KR onay akışı)
│   ├── kr/
│   │   └── kr_registry.md      (KR kayıt defteri — platform kuralları)
│   ├── migration_guides/
│   │   ├── MIGRATION_AUDIT_REPORT_v1_2_0.md (v1.2.0 migrasyon denetim raporu)
│   │   ├── PLATFORM_DEEP_AUDIT_v1_2_0.md (v1.2.0 derin platform denetimi)
│   │   └── README.md
│   ├── runbooks/
│   │   ├── expert_onboarding_procedure.md (Uzman katılım prosedürü)
│   │   ├── incident_response_payment_timeout.md (Ödeme zaman aşımı müdahale)
│   │   ├── incident_response_sla_breach.md (SLA ihlali müdahale)
│   │   ├── payment_approval_procedure.md (Ödeme onay prosedürü)
│   │   └── weather_block_verification_procedure.md (Hava engeli doğrulama prosedürü)
│   ├── security/
│   │   ├── ddos_mitigation_plan.md (DDoS koruma planı)
│   │   └── model_protection_strategy.md (Model koruma stratejisi)
│   └── views/
│       ├── VIEW_3D_GROUPING.md  (3D gruplama görünümü)
│       ├── VIEW_CAPABILITIES.md (Yetenek görünümü)
│       └── VIEW_SDLC.md        (SDLC görünümü)
│
├── scripts/
│   ├── analyze_rate_limit_logs.py (Rate limit log analizi)
│   ├── audit_v322_tree.py       (v3.2.2 ağaç denetim scripti)
│   ├── backup_database.sh       (Veritabanı yedekleme scripti)
│   ├── check_ssot_compliance.py (CI SSOT uyumluluk kontrolü; BOUND header)
│   ├── export_training_dataset.py (Eğitim veri seti dışa aktarma)
│   ├── generate_openapi.py      (OpenAPI şema üretimi)
│   ├── seed_data.py             (Test/demo veri tohumlama)
│   └── seed_experts.py          (Uzman test verisi tohumlama)
│
├── src/
│   ├── __init__.py
│   │
│   ├── application/             (Uygulama katmanı — CQRS, orkestrasyon, servisler)
│   │   ├── __init__.py
│   │   ├── commands/            (CQRS komut nesneleri ve handler'ları)
│   │   │   ├── __init__.py
│   │   │   ├── approve_payment.py (KR-033 ödeme onay komutu; → payment_intent.py)
│   │   │   ├── assign_mission.py (KR-015 görev atama komutu; → mission.py, pilot.py)
│   │   │   ├── calculate_payroll.py (Pilot hakediş hesaplama komutu; → pilot.py)
│   │   │   ├── create_field.py  (KR-013 tarla oluşturma komutu; → field.py)
│   │   │   ├── create_subscription.py (KR-027 abonelik oluşturma komutu; → subscription.py)
│   │   │   ├── register_expert.py (KR-019 uzman kayıt komutu; → expert.py)
│   │   │   ├── report_weather_block.py (KR-015-3A hava engeli rapor komutu; → weather_block_report.py)
│   │   │   ├── schedule_mission.py (KR-015 görev zamanlama komutu; → mission.py)
│   │   │   ├── submit_expert_review.py (KR-019 uzman inceleme gönderim komutu; → expert_review.py)
│   │   │   ├── submit_training_feedback.py (KR-029 eğitim geri bildirim komutu; → feedback_record.py)
│   │   │   └── update_pilot_capacity.py (KR-015-1 pilot kapasite güncelleme; → pilot.py)
│   │   ├── dto/                 (Veri transfer nesneleri — katmanlar arası iletişim)
│   │   │   ├── __init__.py
│   │   │   ├── analysis_result_dto.py (Analiz sonuç DTO; → analysis_result.py)
│   │   │   ├── expert_dashboard_dto.py (Uzman pano DTO; → expert.py, expert_review.py)
│   │   │   ├── expert_dto.py    (Uzman DTO; → expert.py)
│   │   │   ├── expert_review_dto.py (Uzman inceleme DTO; → expert_review.py)
│   │   │   ├── field_dto.py     (Tarla DTO; → field.py)
│   │   │   ├── mission_dto.py   (Görev DTO; → mission.py)
│   │   │   ├── payment_intent_dto.py (Ödeme intent DTO; → payment_intent.py)
│   │   │   ├── pilot_dto.py     (Pilot DTO; → pilot.py)
│   │   │   ├── subscription_dto.py (Abonelik DTO; → subscription.py)
│   │   │   ├── training_export_dto.py (Eğitim dışa aktarım DTO; → feedback_record.py)
│   │   │   ├── user_dto.py      (Kullanıcı DTO; → user.py)
│   │   │   └── weather_block_dto.py (Hava engeli DTO; → weather_block_report.py)
│   │   ├── event_handlers/      (Domain event dinleyicileri)
│   │   │   ├── analysis_completed_handler.py (Analiz tamamlandı → uzman inceleme tetikle; → confidence_evaluator.py)
│   │   │   ├── expert_review_completed_handler.py (İnceleme tamamlandı → training feedback; → feedback_record.py)
│   │   │   ├── mission_lifecycle_handler.py (Görev yaşam döngüsü olayları; → mission.py)
│   │   │   └── subscription_created_handler.py (Abonelik oluşturuldu → görev planlama; → subscription_scheduler.py)
│   │   ├── jobs/                (Zamanlanmış arka plan işleri)
│   │   │   └── weekly_planning_job.py (Haftalık planlama işi; → planning_capacity.py)
│   │   ├── payments/            (Ödeme orkestrasyon modülü)
│   │   │   ├── dtos.py          (Ödeme DTO'ları; → payment_intent.py)
│   │   │   └── service.py       (Ödeme orkestrasyon servisi; → payment_gateway.py)
│   │   ├── queries/             (CQRS sorgu nesneleri)
│   │   │   ├── __init__.py
│   │   │   ├── export_training_data.py (Eğitim verisi dışa aktarım sorgusu)
│   │   │   ├── get_active_price_plans.py (Aktif fiyat planları sorgusu)
│   │   │   ├── get_expert_queue_stats.py (Uzman kuyruk istatistik sorgusu)
│   │   │   ├── get_expert_review_details.py (Uzman inceleme detay sorgusu)
│   │   │   ├── get_field_details.py (Tarla detay sorgusu)
│   │   │   ├── get_mission_timeline.py (Görev zaman çizelgesi sorgusu)
│   │   │   ├── get_pilot_available_slots.py (Pilot müsait slot sorgusu)
│   │   │   ├── get_subscription_details.py (Abonelik detay sorgusu)
│   │   │   ├── list_pending_expert_reviews.py (Bekleyen uzman inceleme listesi)
│   │   │   ├── list_pilot_missions.py (Pilot görev listesi)
│   │   │   └── lookup_parcel_geometry.py (Parsel geometri sorgusu; → TKGM)
│   │   ├── services/            (Uygulama servisleri — iş akışı orkestrasyon)
│   │   │   ├── __init__.py
│   │   │   ├── audit_log_service.py (WORM denetim günlüğü servisi; → audit_log_repository.py)
│   │   │   ├── calibration_gate_service.py (KR-018 kalibrasyon hard gate; → calibration_record.py)
│   │   │   ├── contract_validator_service.py (KR-081 contract doğrulama servisi; → schema_registry.py)
│   │   │   ├── expert_review_service.py (KR-019 uzman inceleme servisi; → expert_review.py)
│   │   │   ├── field_service.py (KR-013 tarla yönetim servisi; → field.py, field_repository.py)
│   │   │   ├── intake_manifest_service.py (KR-072 alım manifest servisi; → dataset.py)
│   │   │   ├── mission_lifecycle_manager.py (KR-028 görev yaşam döngüsü yöneticisi; → mission.py)
│   │   │   ├── mission_service.py (Görev CRUD servisi; → mission_repository.py)
│   │   │   ├── planning_capacity.py (KR-015-1 kapasite planlama; → capacity_manager.py)
│   │   │   ├── pricebook_service.py (KR-022 fiyat kitabı servisi; → price_snapshot.py)
│   │   │   ├── qc_gate_service.py (KR-082 QC gate servisi; → qc_report_record.py)
│   │   │   ├── reassignment_handler.py (Pilot yeniden atama servisi; → mission.py, pilot.py)
│   │   │   ├── subscription_scheduler.py (KR-027 abonelik zamanlayıcı; → subscription.py)
│   │   │   ├── training_export_service.py (Eğitim veri dışa aktarım servisi; → feedback_record.py)
│   │   │   ├── training_feedback_service.py (KR-029 eğitim geri bildirim servisi; → feedback_record.py)
│   │   │   ├── weather_block_service.py (KR-015-3A hava engeli servisi; → weather_block_report.py)
│   │   │   ├── weekly_window_scheduler.py (Haftalık pencere zamanlayıcı; → planning_engine.py)
│   │   │   └── worker_dispatch_service.py (KR-070 worker dispatch servisi; → analysis_job.py)
│   │   └── workers/             (Arka plan worker'ları)
│   │       └── replan_queue_worker.py (Yeniden planlama kuyruk worker'ı; → reassignment_handler.py)
│   │
│   ├── core/                    (Domain çekirdeği — entity, event, value object, port)
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities/        (Domain entity'leri — iş kuralları ve invariant'lar)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis_job.py (Analiz işi; KR-017 izolasyon, KR-018 kalibrasyon gate; → dataset.py)
│   │   │   │   ├── analysis_result.py (Analiz sonucu; KR-025 içerik, KR-081 contract; → analysis_job.py)
│   │   │   │   ├── audit_log_entry.py (WORM denetim kaydı; KR-062 denetlenebilirlik)
│   │   │   │   ├── calibration_record.py (Radyometrik kalibrasyon kaydı; KR-018 hard gate; → dataset.py)
│   │   │   │   ├── dataset.py   (KR-072 dokuz-durum makinesi; KR-073 malware tarama; → calibration_record.py)
│   │   │   │   ├── expert.py    (Uzman; KR-019 curated onboarding, uzmanlık, kota; → expert_review.py)
│   │   │   │   ├── expert_review.py (Uzman inceleme; KR-019 düşük güven → manuel karar; → expert.py)
│   │   │   │   ├── feedback_record.py (Eğitim geri bildirim kaydı; KR-029 model iyileştirme; → expert_review.py)
│   │   │   │   ├── field.py     (Tarla; KR-013 geometri + parsel, KR-016 eşleştirme; → parcel_ref.py)
│   │   │   │   ├── mission.py   (Görev; KR-028 yaşam döngüsü, KR-033 ödeme gate; → pilot.py, field.py)
│   │   │   │   ├── payment_intent.py (Ödeme; KR-033 dekont + manuel onay; → mission.py, subscription.py)
│   │   │   │   ├── pilot.py     (Pilot; KR-015 kapasite, KR-034 drone bağımsızlık; → drone_model.py)
│   │   │   │   ├── price_snapshot.py (Fiyat snapshot; KR-022 immutable fiyat; → pricebook_calculator.py)
│   │   │   │   ├── qc_report_record.py (QC rapor kaydı; KR-018/KR-082 QC gate; → calibration_record.py)
│   │   │   │   ├── subscription.py (Abonelik; KR-027 planlayıcı, KR-015-5 reschedule; → mission.py)
│   │   │   │   ├── user.py      (Kullanıcı; KR-050 telefon+PIN, KR-063 RBAC 13 rol; → role.py)
│   │   │   │   ├── user_pii.py  (KVKK PII izolasyonu; KR-066; → user.py)
│   │   │   │   └── weather_block_report.py (Hava engeli raporu; KR-015-5 force majeure; → mission.py)
│   │   │   ├── events/          (Domain event'leri — immutable olay nesneleri)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis_events.py (Analiz event'leri: AnalysisRequested, Completed; → analysis_job.py)
│   │   │   │   ├── base.py      (DomainEvent taban sınıfı; event_id, occurred_at)
│   │   │   │   ├── expert_events.py (Uzman event'leri: Registered, Activated; → expert.py)
│   │   │   │   ├── expert_review_events.py (İnceleme event'leri: Requested, Completed; → expert_review.py)
│   │   │   │   ├── field_events.py (Tarla event'leri: Created, Updated, CropUpdated; → field.py)
│   │   │   │   ├── mission_events.py (Görev event'leri: Assigned, Started, Completed; → mission.py)
│   │   │   │   ├── payment_events.py (Ödeme event'leri: Created, Approved, Rejected; → payment_intent.py)
│   │   │   │   ├── subscription_events.py (Abonelik event'leri: Created, Activated; → subscription.py)
│   │   │   │   └── training_feedback_events.py (Eğitim feedback event'leri; → feedback_record.py)
│   │   │   ├── services/        (Domain servisleri — saf iş mantığı, IO yok)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auto_dispatcher.py (KR-015 kural bazlı pilot auto-dispatch; → mission.py, pilot.py)
│   │   │   │   ├── band_compliance_checker.py (KR-018/KR-082 band uyumluluk + Graceful Degradation; → drone_model.py, spectral_tier.py)
│   │   │   │   ├── calibration_validator.py (KR-018 radyometrik kalibrasyon doğrulama; → calibration_record.py)
│   │   │   │   ├── capacity_manager.py (KR-015-1 pilot kapasite hesaplama; → pilot.py)
│   │   │   │   ├── confidence_evaluator.py (KR-019 YZ güven değerlendirme → uzman escalation; → ai_confidence.py)
│   │   │   │   ├── coverage_calculator.py (KR-016 mission footprint ↔ field kesişim; → geometry.py)
│   │   │   │   ├── expert_assignment_service.py (KR-019 analiz → uzman eşleştirme; → expert.py)
│   │   │   │   ├── mission_planner.py (Görev planlama kuralları; → capacity_manager.py)
│   │   │   │   ├── plan_window_segmenter.py (KR-015 büyük alan segmentleme; → mission.py)
│   │   │   │   ├── planning_engine.py (KR-015 görev takvimi optimizasyonu; → capacity_manager.py)
│   │   │   │   ├── pricebook_calculator.py (KR-022 fiyat hesaplama + snapshot; → price_snapshot.py)
│   │   │   │   ├── qc_evaluator.py (KR-082 QC değerlendirme ve gate kararı; → qc_report_record.py)
│   │   │   │   ├── reschedule_service.py (KR-015-5 reschedule token yönetimi; → subscription.py)
│   │   │   │   ├── sla_monitor.py (KR-028 SLA takip ve breach algılama; → mission.py)
│   │   │   │   ├── subscription_planner.py (KR-015-5 sezonluk takvim hesaplama; → subscription.py)
│   │   │   │   └── weather_validator.py (KR-015-3A pilot hava raporu kayıt; → weather_block_report.py)
│   │   │   └── value_objects/   (Değer nesneleri — immutable, eşitlik karşılaştırmalı)
│   │   │       ├── __init__.py
│   │   │       ├── ai_confidence.py (YZ güven skoru 0.0–1.0 + eşik kuralları; → confidence_score.py)
│   │   │       ├── assignment_policy.py (KR-015 atama politikası: SYSTEM_SEED | PULL; → auto_dispatcher.py)
│   │   │       ├── av_scan_mode.py (KR-073 malware tarama modu: SMART | BYPASS; → dataset.py)
│   │   │       ├── calibration_manifest.py (KR-018 kalibrasyon kanıt paketi; → calibration_record.py)
│   │   │       ├── confidence_score.py (Model güven skoru 0.0–1.0; → ai_confidence.py)
│   │   │       ├── coverage_ratio_threshold.py (KR-031 uçuş kapsama eşikleri; → coverage_calculator.py)
│   │   │       ├── crop_ops_profile.py (KR-015-1 bitki bazlı kapasite profili; → crop_type.py)
│   │   │       ├── crop_scan_interval.py (KR-024 mahsul tarama aralığı; → subscription_planner.py)
│   │   │       ├── crop_type.py (Bitki tipi enum; → crop_ops_profile.py)
│   │   │       ├── dataset_status.py (KR-072 dokuz+1 durum state machine; → dataset.py)
│   │   │       ├── drone_model.py (KR-030/KR-034 drone model + sensor band; → band_compliance_checker.py)
│   │   │       ├── expert_specialization.py (KR-019 uzman uzmanlık alanları; → expert.py)
│   │   │       ├── geometry.py  (Polygon/Point geometri; Shapely sarmalama; → field.py)
│   │   │       ├── mission_status.py (KR-028 görev durum geçiş kuralları; → mission.py)
│   │   │       ├── money.py     (KR-022 para birimi + kuruş tutar; → price_snapshot.py)
│   │   │       ├── parcel_ref.py (KR-013 il/ilçe/ada/parsel hash tekilleme; → field.py)
│   │   │       ├── payment_status.py (KR-033 ödeme durum enum + gate; → payment_intent.py)
│   │   │       ├── pilot_schedule.py (KR-015 pilot çalışma günleri + kapasite; → pilot.py)
│   │   │       ├── price_snapshot.py (KR-022 immutable fiyat snapshot; → pricebook_calculator.py)
│   │   │       ├── province.py  (KR-083 Türkiye 81 il listesi + bölge yetkisi; → pilot.py)
│   │   │       ├── qc_flag.py   (KR-018 spesifik QC kontrol bayrakları; → qc_evaluator.py)
│   │   │       ├── qc_report.py (KR-082 QC raporu + threshold kuralları; → qc_evaluator.py)
│   │   │       ├── qc_status.py (KR-082 QC durum enum; → qc_report_record.py)
│   │   │       ├── recommended_action.py (KR-082 QC sonrası aksiyon önerisi; → qc_evaluator.py)
│   │   │       ├── role.py      (KR-063 RBAC rolleri ve yetki kapsamları; → user.py)
│   │   │       ├── sla_metrics.py (Mission SLA metrikleri; → sla_monitor.py)
│   │   │       ├── sla_threshold.py (Servis seviyesi eşikleri; → sla_monitor.py)
│   │   │       ├── specialization.py (KR-019 uzman uzmanlık alanları enum; → expert.py)
│   │   │       ├── spectral_tier.py (KR-018/KR-082 Graceful Degradation band sınıflandırma; → band_compliance_checker.py)
│   │   │       ├── subscription_plan.py (Abonelik plan detayları; → subscription.py)
│   │   │       ├── training_grade.py (Eğitim veri kalite derecesi A–D|REJECT; → feedback_record.py)
│   │   │       └── weather_block_status.py (KR-015-3A hava engeli rapor durumu; → weather_block_report.py)
│   │   └── ports/               (Port arayüzleri — bağımlılık tersine çevirme)
│   │       ├── __init__.py
│   │       ├── external/        (Dış servis port'ları — Protocol tabanlı)
│   │       │   ├── __init__.py
│   │       │   ├── ai_worker_feedback.py (KR-019/KR-029 YZ feedback loop portu; → feedback_record.py)
│   │       │   ├── av_scanner_port.py (KR-073 malware tarama portu; → dataset.py)
│   │       │   ├── ddos_protection.py (DDoS koruma sağlayıcı portu; → cloudflare/)
│   │       │   ├── parcel_geometry_provider.py (TKGM/MEGSİS parsel geometri portu; → field.py)
│   │       │   ├── payment_gateway.py (KR-033 ödeme sağlayıcı portu; → payment_intent.py)
│   │       │   ├── sms_gateway.py (SMS gönderim portu; → netgsm.py, twilio.py)
│   │       │   └── storage_service.py (Nesne depolama portu; → s3_storage.py)
│   │       ├── messaging/       (Mesajlaşma port'ları)
│   │       │   ├── __init__.py
│   │       │   └── event_bus.py (Event publish/subscribe portu; → rabbitmq_event_bus_impl.py)
│   │       └── repositories/   (Veri erişim port'ları — Protocol tabanlı)
│   │           ├── __init__.py
│   │           ├── analysis_result_repository.py (Analiz sonuç repository portu)
│   │           ├── audit_log_repository.py (Denetim günlüğü repository portu)
│   │           ├── calibration_record_repository.py (Kalibrasyon kayıt repository portu)
│   │           ├── crop_ops_profile_repository.py (Bitki profili repository portu)
│   │           ├── dataset_repository.py (KR-072 dataset repository portu)
│   │           ├── expert_repository.py (Uzman repository portu)
│   │           ├── expert_review_repository.py (Uzman inceleme repository portu)
│   │           ├── feedback_record_repository.py (Geri bildirim kayıt repository portu)
│   │           ├── field_repository.py (Tarla repository portu)
│   │           ├── mission_repository.py (Görev repository portu)
│   │           ├── payment_intent_repository.py (Ödeme intent repository portu)
│   │           ├── pilot_repository.py (Pilot repository portu)
│   │           ├── price_snapshot_repository.py (Fiyat snapshot repository portu)
│   │           ├── qc_report_repository.py (QC rapor repository portu)
│   │           ├── subscription_repository.py (Abonelik repository portu)
│   │           ├── user_repository.py (Kullanıcı repository portu)
│   │           ├── weather_block_report_repository.py (Hava engeli rapor repository portu)
│   │           └── weather_block_repository.py (Hava engeli repository portu)
│   │
│   ├── infrastructure/          (Altyapı katmanı — adaptörler, persistence, entegrasyon)
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   ├── drone_registry.yaml (Drone kayıt verisi; → drone_registry_loader.py)
│   │   │   └── settings.py      (pydantic-settings ENV yükleme; → .env.example)
│   │   ├── contracts/
│   │   │   ├── __init__.py
│   │   │   ├── contract_validator_adapter.py (KR-081 ContractValidatorPort adaptörü; → schema_registry.py, contract_validator_service.py)
│   │   │   └── schema_registry.py (KR-081 JSON Schema yükleme + cache; → contracts/)
│   │   ├── external/            (Dış servis adaptörleri — port implementasyonları)
│   │   │   ├── __init__.py
│   │   │   ├── av_scanner_client.py (KR-073 AV tarama istemcisi; → av_scanner_port.py)
│   │   │   ├── drone_registry_loader.py (Drone kayıt YAML yükleyici; → drone_registry.yaml)
│   │   │   ├── payment_gateway_adapter.py (KR-033 ödeme gateway adaptörü; → payment_gateway.py)
│   │   │   ├── sms_gateway_adapter.py (SMS gateway adaptörü; → sms_gateway.py)
│   │   │   ├── storage_adapter.py (Nesne depolama adaptörü; → storage_service.py)
│   │   │   ├── tkgm_megsis_wfs_adapter.py (TKGM/MEGSİS WFS parsel geometri; → parcel_geometry_provider.py)
│   │   │   └── weather_api_adapter.py (Hava durumu API adaptörü)
│   │   ├── integrations/        (Üçüncü parti entegrasyonlar)
│   │   │   ├── __init__.py
│   │   │   ├── cloudflare/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ddos_protection.py (Cloudflare DDoS koruma impl; → ddos_protection.py port)
│   │   │   ├── payments/
│   │   │   │   ├── __init__.py
│   │   │   │   └── provider_gateway.py (Ödeme sağlayıcı gateway impl; → payment_gateway.py port)
│   │   │   ├── sms/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── netgsm.py   (NetGSM SMS impl; → sms_gateway.py port)
│   │   │   │   └── twilio.py   (Twilio SMS impl; → sms_gateway.py port)
│   │   │   └── storage/
│   │   │       ├── __init__.py
│   │   │       └── s3_storage.py (AWS S3 depolama impl; → storage_service.py port)
│   │   ├── messaging/           (Mesajlaşma altyapısı)
│   │   │   ├── __init__.py
│   │   │   ├── event_publisher.py (Genel event yayınlayıcı; → event_bus.py port)
│   │   │   ├── rabbitmq_config.py (RabbitMQ bağlantı ayarları)
│   │   │   ├── rabbitmq_event_bus_impl.py (RabbitMQ EventBus impl; → event_bus.py port)
│   │   │   ├── rabbitmq/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_feedback_publisher.py (YZ feedback RabbitMQ publisher; → ai_worker_feedback.py)
│   │   │   │   ├── consumer.py  (RabbitMQ mesaj tüketici)
│   │   │   │   ├── publisher.py (RabbitMQ mesaj yayınlayıcı)
│   │   │   │   └── training_feedback_publisher.py (Eğitim feedback publisher; → feedback_record.py)
│   │   │   └── websocket/
│   │   │       ├── __init__.py
│   │   │       └── notification_manager.py (WebSocket bildirim yöneticisi)
│   │   ├── monitoring/          (Gözlemlenebilirlik altyapısı)
│   │   │   ├── __init__.py
│   │   │   ├── health_checks.py (Sağlık kontrol endpoint'leri; DB, Redis, RabbitMQ)
│   │   │   ├── prometheus_metrics.py (Prometheus metrik tanımları)
│   │   │   └── security_events.py (Güvenlik olay izleme; → audit_log_service.py)
│   │   ├── notifications/
│   │   │   └── pilot_notification_service.py (Pilot SMS/push bildirim servisi; → sms_gateway.py)
│   │   ├── persistence/         (Veri kalıcılık katmanı)
│   │   │   ├── __init__.py
│   │   │   ├── database.py      (Veritabanı bağlantı yönetimi; → settings.py)
│   │   │   ├── models/
│   │   │   │   ├── crop_ops_profile_model.py (Bitki profili DB modeli; → crop_ops_profile.py)
│   │   │   │   ├── mission_segment_model.py (Görev segment DB modeli; → plan_window_segmenter.py)
│   │   │   │   ├── payment_intent_model.py (Ödeme intent DB modeli; → payment_intent.py)
│   │   │   │   ├── reschedule_request_model.py (Yeniden planlama talep modeli; → reschedule_service.py)
│   │   │   │   └── weather_block_report_model.py (Hava engeli rapor DB modeli; → weather_block_report.py)
│   │   │   ├── redis/
│   │   │   │   ├── cache.py     (Redis önbellek yönetimi; → settings.py)
│   │   │   │   └── rate_limiter.py (Redis tabanlı rate limiter; → rate_limit_middleware.py)
│   │   │   ├── repositories/
│   │   │   │   ├── mission_segment_repository.py (Görev segment repository impl)
│   │   │   │   └── reschedule_repository.py (Yeniden planlama repository impl)
│   │   │   └── sqlalchemy/
│   │   │       ├── __init__.py
│   │   │       ├── base.py      (SQLAlchemy DeclarativeBase; tüm modeller)
│   │   │       ├── models.py    (SQLAlchemy model kayıtları)
│   │   │       ├── session.py   (SQLAlchemy oturum fabrikası; → database.py)
│   │   │       ├── unit_of_work.py (Unit of Work pattern impl)
│   │   │       ├── migrations/
│   │   │       │   └── versions/
│   │   │       │       ├── 2026_01_26_add_expert_portal_tables.py (Uzman portal tabloları)
│   │   │       │       ├── 2026_01_27_add_v2_6_0_tables.py (v2.6.0 tablo ekleme)
│   │   │       │       └── 2026_02_02_add_pricebook_tables.py (Fiyat kitabı tabloları)
│   │   │       ├── models/      (SQLAlchemy ORM modelleri — entity eşleştirme)
│   │   │       │   ├── __init__.py
│   │   │       │   ├── analysis_job_model.py (AnalysisJob ORM; → analysis_job.py)
│   │   │       │   ├── analysis_result_model.py (AnalysisResult ORM; → analysis_result.py)
│   │   │       │   ├── audit_log_model.py (AuditLogEntry ORM; → audit_log_entry.py)
│   │   │       │   ├── expert_model.py (Expert ORM; → expert.py)
│   │   │       │   ├── expert_review_model.py (ExpertReview ORM; → expert_review.py)
│   │   │       │   ├── field_model.py (Field ORM; → field.py)
│   │   │       │   ├── mission_model.py (Mission ORM; → mission.py)
│   │   │       │   ├── payment_intent_model.py (PaymentIntent ORM; → payment_intent.py)
│   │   │       │   ├── pilot_model.py (Pilot ORM; → pilot.py)
│   │   │       │   ├── price_snapshot_model.py (PriceSnapshot ORM; → price_snapshot.py)
│   │   │       │   ├── subscription_model.py (Subscription ORM; → subscription.py)
│   │   │       │   ├── user_model.py (User ORM; → user.py)
│   │   │       │   └── weather_block_model.py (WeatherBlock ORM; → weather_block_report.py)
│   │   │       └── repositories/ (Repository port implementasyonları — SQLAlchemy)
│   │   │           ├── __init__.py
│   │   │           ├── analysis_result_repository_impl.py (→ analysis_result_repository.py)
│   │   │           ├── audit_log_repository_impl.py (→ audit_log_repository.py)
│   │   │           ├── calibration_record_repository_impl.py (→ calibration_record_repository.py)
│   │   │           ├── crop_ops_profile_repository_impl.py (→ crop_ops_profile_repository.py)
│   │   │           ├── dataset_repository_impl.py (→ dataset_repository.py)
│   │   │           ├── expert_repository_impl.py (→ expert_repository.py)
│   │   │           ├── expert_review_repository_impl.py (→ expert_review_repository.py)
│   │   │           ├── feedback_record_repository_impl.py (→ feedback_record_repository.py)
│   │   │           ├── field_repository_impl.py (→ field_repository.py)
│   │   │           ├── mission_repository_impl.py (→ mission_repository.py)
│   │   │           ├── payment_intent_repository_impl.py (→ payment_intent_repository.py)
│   │   │           ├── pilot_repository_impl.py (→ pilot_repository.py)
│   │   │           ├── price_snapshot_repository_impl.py (→ price_snapshot_repository.py)
│   │   │           ├── qc_report_repository_impl.py (→ qc_report_repository.py)
│   │   │           ├── subscription_repository_impl.py (→ subscription_repository.py)
│   │   │           ├── user_repository_impl.py (→ user_repository.py)
│   │   │           ├── weather_block_report_repository_impl.py (→ weather_block_report_repository.py)
│   │   │           └── weather_block_repository_impl.py (→ weather_block_repository.py)
│   │   └── security/           (Güvenlik altyapısı)
│   │       ├── encryption.py    (Şifreleme servisi; AES-256; → user_pii.py)
│   │       ├── jwt_handler.py   (JWT token üretim/doğrulama; → jwt_middleware.py)
│   │       ├── query_pattern_analyzer.py (SQL injection algılama; → anomaly_detection_middleware.py)
│   │       └── rate_limit_config.py (Rate limit kural ayrıştırma; → rate_limit_middleware.py)
│   │
│   └── presentation/           (Sunum katmanı — API, CLI)
│       ├── __init__.py
│       ├── api/                 (FastAPI HTTP API)
│       │   ├── __init__.py
│       │   ├── dependencies.py  (FastAPI DI bağımlılıkları ve HTTP hook'ları; → tüm endpoint'ler)
│       │   ├── main.py          (FastAPI app entrypoint ve middleware wiring; → settings.py, tüm endpoint'ler)
│       │   ├── service_factory.py (Servis fabrikası; DI container; → tüm servisler)
│       │   ├── settings.py      (API ayarları; CORS, güvenlik; → main.py)
│       │   ├── middleware/      (HTTP middleware zincirleri)
│       │   │   ├── _shared.py   (Middleware ortak yardımcılar)
│       │   │   ├── anomaly_detection_middleware.py (KR-033 anomali algılama; → query_pattern_analyzer.py)
│       │   │   ├── cors_middleware.py (CORS ayarları; → main.py)
│       │   │   ├── grid_anonymizer.py (KR-083 İl Operatörü koordinat anonimizasyonu; → pii_filter.py)
│       │   │   ├── jwt_middleware.py (JWT doğrulama middleware; → jwt_handler.py)
│       │   │   ├── mtls_verifier.py (KR-071 mTLS cihaz kimlik doğrulama; → ingest.py)
│       │   │   ├── pii_filter.py (KR-066 PII sızma engelleme; → user_pii.py)
│       │   │   ├── rate_limit_middleware.py (KR-050 rate limiting; → rate_limiter.py)
│       │   │   └── rbac_middleware.py (KR-063 RBAC yetki kontrolü; 13 rol matrisi; → jwt_middleware.py)
│       │   └── v1/              (API v1 endpoint'leri)
│       │       ├── __init__.py
│       │       ├── endpoints/   (REST endpoint modülleri)
│       │       │   ├── __init__.py
│       │       │   ├── admin_audit.py (KR-063 admin denetim günlüğü; → audit_log_service.py)
│       │       │   ├── admin_payments.py (KR-033 admin ödeme yönetimi; → payment_intent.py)
│       │       │   ├── admin_pricing.py (KR-081 admin fiyat yönetimi; → pricebook_service.py)
│       │       │   ├── auth.py  (KR-050 kimlik doğrulama; telefon+PIN; → jwt_handler.py)
│       │       │   ├── calibration.py (KR-018 kalibrasyon endpoint'leri; → calibration_gate_service.py)
│       │       │   ├── expert_portal.py (KR-019/KR-063 uzman portal; → expert_review_service.py)
│       │       │   ├── experts.py (KR-063 uzman yönetim; → expert.py)
│       │       │   ├── fields.py (KR-013/KR-081 tarla CRUD; → field_service.py)
│       │       │   ├── ingest.py (KR-072 dataset alım; mTLS zorunlu; → intake_manifest_service.py)
│       │       │   ├── missions.py (KR-015 görev yönetimi; → mission_service.py)
│       │       │   ├── parcels.py (KR-013 parsel geometri; → parcel_geometry_provider.py)
│       │       │   ├── payment_webhooks.py (KR-033 ödeme webhook callback; → payment_intent.py)
│       │       │   ├── payments.py (KR-033 ödeme akışı; → payment_intent.py)
│       │       │   ├── pilots.py (KR-015 pilot yönetimi; → pilot.py)
│       │       │   ├── pricing.py (KR-033 herkese açık fiyat listesi; → pricebook_service.py)
│       │       │   ├── qc.py    (KR-082 QC rapor endpoint'leri; → qc_gate_service.py)
│       │       │   ├── results.py (KR-017 analiz sonuç; → analysis_result.py)
│       │       │   ├── sla_metrics.py (KR-083 İl Operatörü KPI metrikleri; → sla_monitor.py)
│       │       │   ├── subscriptions.py (KR-027 abonelik yönetimi; → subscription_scheduler.py)
│       │       │   ├── training_feedback.py (KR-029 eğitim geri bildirim; → training_feedback_service.py)
│       │       │   ├── weather_block_reports.py (KR-015-3A hava engeli rapor; → weather_block_service.py)
│       │       │   └── weather_blocks.py (KR-015 hava engeli yönetimi; → weather_block_service.py)
│       │       └── schemas/     (Pydantic API şemaları — istek/yanıt modelleri)
│       │           ├── expert_review_schemas.py (Uzman inceleme istek/yanıt; → expert_review.py)
│       │           ├── expert_schemas.py (Uzman istek/yanıt; → expert.py)
│       │           ├── field_schemas.py (Tarla istek/yanıt; → field.py)
│       │           ├── mission_schemas.py (Görev istek/yanıt; → mission.py)
│       │           ├── parcel_schemas.py (Parsel istek/yanıt; → parcel_ref.py)
│       │           ├── payment_webhook_schemas.py (Ödeme webhook şemaları; → payment_intent.py)
│       │           ├── subscription_schemas.py (Abonelik istek/yanıt; → subscription.py)
│       │           ├── training_feedback_schemas.py (Eğitim feedback şemaları; → feedback_record.py)
│       │           └── weather_block_schemas.py (Hava engeli istek/yanıt; → weather_block_report.py)
│       └── cli/                 (Komut satırı arayüzü)
│           ├── __init__.py
│           ├── __main__.py      (CLI giriş noktası; python -m src.presentation.cli)
│           ├── main.py          (Typer CLI uygulama tanımı; → tüm commands/)
│           └── commands/        (CLI alt komutları)
│               ├── __init__.py
│               ├── expert_management.py (Uzman yönetim komutları; → expert.py)
│               ├── migrate.py   (Veritabanı migrasyon komutları; → alembic)
│               ├── run_weekly_planner.py (Haftalık planlama çalıştırma; → weekly_planning_job.py)
│               ├── seed.py      (Test verisi tohumlama; → seed_data.py)
│               └── subscription_management.py (Abonelik yönetim komutları; → subscription.py)
│
├── tests/                       (Test dizini — unit, integration, e2e, security, performance)
│   ├── __init__.py
│   ├── conftest.py              (Pytest global fixture ve konfigürasyon; → domain_fixtures.py)
│   ├── e2e/                     (Uçtan uca testler)
│   │   ├── __init__.py
│   │   ├── test_expert_journey.py (Uzman iş akışı e2e testi; → expert_portal.py)
│   │   ├── test_farmer_journey.py (Çiftçi iş akışı e2e testi; → fields.py, missions.py, results.py)
│   │   ├── test_payment_flow.py (Ödeme akışı e2e testi; → payments.py, payment_webhooks.py)
│   │   └── test_pilot_journey.py (Pilot iş akışı e2e testi; → pilots.py, weather_blocks.py)
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── domain_fixtures.py   (Domain entity test fabrikaları; → tüm entities/)
│   ├── integration/             (Entegrasyon testleri)
│   │   ├── __init__.py
│   │   ├── test_api_calibration_qc.py (KR-018 kalibrasyon/QC hard gate testi; → calibration.py, qc.py)
│   │   ├── test_api_fields.py   (Tarla API testi; → fields.py)
│   │   ├── test_api_payments_and_webhooks.py (KR-033 ödeme + webhook testi; → payments.py)
│   │   ├── test_api_weather_block_reports.py (KR-015 hava engeli rapor testi; → weather_block_reports.py)
│   │   ├── test_event_bus.py    (EventBus entegrasyon testi; → rabbitmq_event_bus_impl.py)
│   │   ├── test_field_repository.py (Tarla repository testi; → field_repository_impl.py)
│   │   └── test_mission_repository.py (Görev repository testi; → mission_repository_impl.py)
│   ├── performance/             (Performans testleri)
│   │   ├── __init__.py
│   │   ├── locustfile.py        (Locust yük testi tanımı)
│   │   └── test_mission_assignment_load.py (Görev atama yük testi; → assign_mission.py)
│   ├── presentation/            (Sunum katmanı testleri)
│   │   ├── api/
│   │   │   ├── test_main.py     (FastAPI app başlatma testi; → main.py)
│   │   │   ├── test_v1_calibration_qc_sla.py (KR-041 kalibrasyon/QC/SLA endpoint testi)
│   │   │   ├── test_v1_payments_admin.py (KR-033 admin ödeme endpoint testi)
│   │   │   └── middleware/
│   │   │       ├── test_anomaly_detection_middleware.py (Anomali algılama testi; → anomaly_detection_middleware.py)
│   │   │       ├── test_cors_middleware.py (CORS testi; → cors_middleware.py)
│   │   │       ├── test_jwt_middleware.py (JWT testi; → jwt_middleware.py)
│   │   │       └── test_rate_limit_middleware.py (Rate limit testi; → rate_limit_middleware.py)
│   │   └── cli/
│   │       └── test_cli_main.py (CLI giriş testi; → main.py)
│   ├── security/                (Güvenlik testleri)
│   │   ├── __init__.py
│   │   ├── test_brute_force_lockout.py (SC-SEC-02 brute force kilitleme; 16 fail → 30 dk lock)
│   │   ├── test_grid_anonymization.py (KR-083 İl Operatörü koordinat anonimizasyonu)
│   │   ├── test_mtls_verification.py (KR-071 mTLS cihaz kimlik doğrulama)
│   │   ├── test_pii_filter.py   (SC-SEC-05 PII sızma testi; İl Operatörü PII göremez)
│   │   ├── test_rate_limit_enforcement.py (SC-SEC-01 rate limit 61 req/min → 429)
│   │   ├── test_rbac_middleware.py (KR-063 RBAC middleware testi; 13 rol matrisi)
│   │   ├── test_rbac_pilot_results_403.py (KR-063/KR-017 Pilot sonuç göremez testi)
│   │   └── test_webhook_replay_protection.py (KR-033 webhook replay saldırı önleme)
│   └── unit/                    (Birim testleri)
│       ├── __init__.py
│       ├── test_analysis_completed_handler.py (KR-019 analiz tamamlandı handler testi)
│       ├── test_analysis_result_v120.py (KR-025/KR-081 analiz sonuç v1.2.0 testi)
│       ├── test_band_compliance_v120.py (KR-018/KR-082 band uyumluluk Graceful Degradation testi)
│       ├── test_calibration_gate.py (KR-018 kalibrasyon hard gate testi)
│       ├── test_dataset_bands.py (KR-018/KR-072 dataset available_bands testi)
│       ├── test_drone_model_v120.py (KR-030/KR-034 drone model v1.2.0 testi)
│       ├── test_payment_intent_dto.py (KR-033 ödeme intent DTO testi)
│       ├── test_payment_intent_manual_approval.py (KR-033 manuel onay testi)
│       ├── test_spectral_tier.py (KR-018/KR-082 SpectralTier Graceful Degradation testi)
│       ├── test_ssot_compliance_script.py (KR-041 SSOT CI script testi)
│       ├── test_weather_block_replan.py (Hava engeli yeniden planlama testi)
│       ├── application/
│       │   ├── commands/
│       │   │   ├── test_assign_mission.py (KR-015 görev atama komut testi)
│       │   │   ├── test_contract_validation.py (KR-081 contract doğrulama testi)
│       │   │   └── test_create_field.py (KR-013 tarla oluşturma komut testi)
│       │   └── services/
│       │       ├── test_application_services.py (KR-018 QC kararı birim testi)
│       │       └── test_payment_orchestration.py (Ödeme orkestrasyon testi)
│       ├── domain/
│       │   ├── entities/
│       │   │   ├── test_field.py (Tarla entity testi; → field.py)
│       │   │   ├── test_mission.py (Görev entity testi; KR-028, KR-033; → mission.py)
│       │   │   ├── test_payment_intent.py (Ödeme intent entity testi; → payment_intent.py)
│       │   │   └── test_subscription.py (Abonelik entity testi; KR-027/KR-015-5; → subscription.py)
│       │   ├── services/
│       │   │   ├── test_capacity_manager.py (Kapasite yöneticisi testi; → capacity_manager.py)
│       │   │   └── test_planning_engine.py (Planlama motoru testi; → planning_engine.py)
│       │   └── value_objects/
│       │       ├── test_geometry.py (Geometri VO testi; → geometry.py)
│       │       └── test_parcel_ref.py (Parsel referansı VO testi; → parcel_ref.py)
│       └── infrastructure/
│           └── security/
│               └── test_security_stabilization.py (Güvenlik altyapı testi; → encryption.py, jwt_handler.py)
│
└── web/                         (Next.js frontend — PWA)
    ├── .env.example             (Frontend ortam değişkenleri şablonu)
    ├── .storybook/
    │   ├── main.ts              (Storybook yapılandırması)
    │   └── preview.ts           (Storybook önizleme ayarları)
    ├── README.md                (Frontend kurulum ve geliştirme rehberi)
    ├── eslint.config.mjs        (ESLint yapılandırması)
    ├── jest.config.js           (Jest test yapılandırması)
    ├── next-env.d.ts            (Next.js TypeScript ortam tanımları)
    ├── next.config.mjs          (Next.js yapılandırması; PWA, Sentry)
    ├── package-lock.json        (npm bağımlılık kilidi)
    ├── package.json             (Node.js bağımlılıkları ve scriptler)
    ├── playwright.config.ts     (Playwright e2e test yapılandırması)
    ├── pnpm-lock.yaml           (pnpm bağımlılık kilidi)
    ├── postcss.config.mjs       (PostCSS yapılandırması; Tailwind)
    ├── sentry.client.config.ts  (Sentry istemci hata izleme yapılandırması)
    ├── sentry.server.config.ts  (Sentry sunucu hata izleme yapılandırması)
    ├── tailwind.config.ts       (Tailwind CSS yapılandırması)
    ├── tsconfig.json            (TypeScript derleyici ayarları)
    ├── e2e/
    │   └── tests/
    │       ├── auth.spec.ts     (Kimlik doğrulama e2e testi)
    │       ├── expert_journey.spec.ts (Uzman iş akışı e2e testi)
    │       └── farmer_journey.spec.ts (Çiftçi iş akışı e2e testi)
    ├── public/
    │   ├── manifest.json        (PWA manifest dosyası)
    │   ├── robots.txt           (Arama motoru tarama kuralları)
    │   ├── service-worker.js    (PWA service worker; offline destek)
    │   ├── icons/
    │   │   ├── icon-192x192.png (PWA küçük ikon)
    │   │   └── icon-512x512.png (PWA büyük ikon)
    │   └── sounds/
    │       └── notification.mp3 (Bildirim sesi)
    ├── scripts/
    │   └── ci/
    │       └── run.mjs          (Frontend CI çalıştırma scripti)
    └── src/
        ├── middleware.ts         (Next.js auth + RBAC route guard; → routes.ts, useAuth.ts)
        ├── app/                  (Next.js App Router sayfa yapısı)
        │   ├── error.tsx         (Global hata sayfası)
        │   ├── layout.tsx        (Root layout; metadata, font, provider)
        │   ├── loading.tsx       (Root yükleniyor durumu)
        │   ├── not-found.tsx     (404 sayfası)
        │   ├── page.tsx          (Ana sayfa; rol bazlı yönlendirme)
        │   ├── robots.ts         (robots.txt üretimi)
        │   ├── sitemap.ts        (sitemap.xml üretimi)
        │   ├── (admin)/          (Admin panel sayfaları — CENTRAL_ADMIN, BILLING_ADMIN)
        │   │   ├── layout.tsx    (Admin layout; navigasyon, rol guard)
        │   │   ├── loading.tsx   (Admin yükleniyor durumu)
        │   │   ├── admin/
        │   │   │   ├── payments/
        │   │   │   │   └── page.tsx (KR-033 ödeme yönetim sayfası)
        │   │   │   └── sla/
        │   │   │       └── page.tsx (SLA metrik izleme sayfası)
        │   │   ├── analytics/
        │   │   │   └── page.tsx  (Analitik dashboard sayfası)
        │   │   ├── api-keys/
        │   │   │   └── page.tsx  (API anahtar yönetim sayfası)
        │   │   ├── audit/
        │   │   │   └── page.tsx  (KR-033 denetim günlüğü sayfası)
        │   │   ├── audit-viewer/
        │   │   │   └── page.tsx  (Denetim kayıt görüntüleyici)
        │   │   ├── billing/
        │   │   │   ├── payments/
        │   │   │   │   └── page.tsx (KR-033 BILLING_ADMIN IBAN onay; T+1 SLA)
        │   │   │   └── refunds/
        │   │   │       └── page.tsx (KR-033 iade yönetimi; CENTRAL_ADMIN)
        │   │   ├── calibration/
        │   │   │   └── page.tsx  (KR-018 kalibrasyon izleme sayfası)
        │   │   ├── dashboard/
        │   │   │   └── page.tsx  (Admin dashboard)
        │   │   ├── expert-management/
        │   │   │   └── page.tsx  (Uzman yönetim sayfası)
        │   │   ├── experts/
        │   │   │   └── page.tsx  (Uzman listesi sayfası)
        │   │   ├── il/           (KR-083 İl Operatörü sayfaları — PII görmez)
        │   │   │   ├── dashboard/
        │   │   │   │   └── page.tsx (İl Operatörü KPI dashboard; KR-066 PII yok)
        │   │   │   └── metrics/
        │   │   │       └── page.tsx (İl Operatörü operasyon metrikleri)
        │   │   ├── pilots/
        │   │   │   └── page.tsx  (KR-015 pilot yönetim sayfası)
        │   │   ├── price-management/
        │   │   │   └── page.tsx  (Fiyat yönetim sayfası)
        │   │   ├── pricing/
        │   │   │   └── page.tsx  (Fiyat listesi sayfası)
        │   │   ├── qc/
        │   │   │   └── page.tsx  (KR-082 QC izleme sayfası)
        │   │   └── users/
        │   │       └── page.tsx  (Kullanıcı yönetim sayfası)
        │   ├── (auth)/           (Kimlik doğrulama sayfaları)
        │   │   ├── layout.tsx    (Auth layout; minimal)
        │   │   ├── login/
        │   │   │   └── page.tsx  (KR-050 giriş sayfası; telefon + PIN)
        │   │   └── register/
        │   │       └── page.tsx  (KR-050/KR-013 kayıt sayfası; il, ilçe, ad, telefon)
        │   ├── (expert)/         (Uzman portal sayfaları — EXPERT rolü)
        │   │   ├── layout.tsx    (Uzman layout; navigasyon, rol guard)
        │   │   ├── expert/
        │   │   │   ├── profile/
        │   │   │   │   └── page.tsx (Uzman profil sayfası)
        │   │   │   ├── settings/
        │   │   │   │   └── page.tsx (Uzman ayarlar sayfası)
        │   │   │   └── sla/
        │   │   │       └── page.tsx (Uzman SLA metrikleri)
        │   │   ├── queue/
        │   │   │   └── page.tsx  (KR-019 uzman iş kuyruğu; bekleyen incelemeler)
        │   │   ├── review/
        │   │   │   └── [reviewId]/
        │   │   │       └── page.tsx (KR-019 tekil inceleme detay sayfası)
        │   │   └── reviews/
        │   │       └── [id]/
        │   │           └── page.tsx (İnceleme detay sayfası)
        │   ├── (farmer)/         (Çiftçi sayfaları — FARMER_SINGLE, FARMER_MEMBER, COOP_*)
        │   │   ├── layout.tsx    (Çiftçi layout; navigasyon, rol guard)
        │   │   ├── loading.tsx   (Çiftçi yükleniyor durumu)
        │   │   ├── coop/         (KR-014 kooperatif yönetimi)
        │   │   │   ├── dashboard/
        │   │   │   │   └── page.tsx (Kooperatif dashboard; COOP_OWNER)
        │   │   │   ├── fields/
        │   │   │   │   └── page.tsx (Kooperatif tarla listesi)
        │   │   │   ├── invite/
        │   │   │   │   └── page.tsx (KR-014 üye davet; QR/kod/CSV)
        │   │   │   └── members/
        │   │   │       └── page.tsx (Kooperatif üye yönetimi)
        │   │   ├── fields/
        │   │   │   ├── page.tsx  (Çiftçi tarla listesi)
        │   │   │   └── [id]/
        │   │   │       └── page.tsx (Tarla detay sayfası)
        │   │   ├── missions/
        │   │   │   ├── page.tsx  (Çiftçi görev listesi)
        │   │   │   └── [id]/
        │   │   │       └── page.tsx (Görev detay sayfası)
        │   │   ├── payments/
        │   │   │   └── page.tsx  (KR-033 ödeme sayfası; dekont yükleme)
        │   │   ├── profile/
        │   │   │   └── page.tsx  (Çiftçi profil sayfası)
        │   │   ├── results/
        │   │   │   ├── page.tsx  (KR-018 analiz sonuç listesi)
        │   │   │   └── [missionId]/
        │   │   │       └── page.tsx (KR-025/KR-026 görev sonuç harita görünümü)
        │   │   └── subscriptions/
        │   │       ├── page.tsx  (Abonelik listesi)
        │   │       └── create/
        │   │           └── page.tsx (KR-027 sezonluk paket oluşturma)
        │   ├── (pilot)/          (Pilot sayfaları — PILOT rolü)
        │   │   ├── layout.tsx    (Pilot layout; navigasyon, rol guard)
        │   │   ├── loading.tsx   (Pilot yükleniyor durumu)
        │   │   ├── capacity/
        │   │   │   └── page.tsx  (KR-015 kapasite/çalışma günü ayarları)
        │   │   ├── pilot/
        │   │   │   ├── missions/
        │   │   │   │   └── page.tsx (Pilot görev listesi)
        │   │   │   ├── profile/
        │   │   │   │   └── page.tsx (Pilot profil sayfası)
        │   │   │   └── settings/
        │   │   │       └── page.tsx (Pilot ayarlar sayfası)
        │   │   ├── planner/
        │   │   │   └── page.tsx  (KR-015 planlama görünümü)
        │   │   └── weather-block/
        │   │       └── page.tsx  (KR-015-3A hava engeli bildirimi)
        │   ├── api/
        │   │   └── health/
        │   │       └── route.ts  (Frontend health check API route)
        │   └── forbidden/
        │       └── page.tsx      (403 yetkisiz erişim sayfası)
        ├── components/           (React bileşenleri)
        │   ├── common/           (Ortak yardımcı bileşenler)
        │   │   ├── AccessibilityProvider.tsx (Erişilebilirlik bağlam sağlayıcı)
        │   │   ├── ConfirmDialog.tsx (Onay dialog bileşeni)
        │   │   ├── EmptyState.tsx (Boş durum gösterimi)
        │   │   ├── LoadingSpinner.tsx (Yükleniyor spinner)
        │   │   └── ToastProvider.tsx (Toast bildirim sağlayıcı; → useToast.ts)
        │   ├── features/         (Alan bazlı bileşenler)
        │   │   ├── admin/
        │   │   │   ├── AuditLogTable.tsx (Denetim günlüğü tablosu; → useAuditLogs.ts)
        │   │   │   └── SlaDashboard.tsx (SLA KPI dashboard; → sla_metrics.py)
        │   │   ├── dataset/
        │   │   │   └── DatasetUploadModal.tsx (Pilot dataset yükleme modal; → useUpload.ts)
        │   │   ├── expert/
        │   │   │   └── AnnotationCanvas.tsx (Uzman inceleme annotation canvas; → useExpertReview.ts)
        │   │   ├── field/
        │   │   │   ├── AddFieldModal.tsx (KR-013 tarla ekleme modal; → useFields.ts)
        │   │   │   ├── FieldList.tsx (Tarla listesi bileşeni; → useFields.ts)
        │   │   │   └── FieldMap.tsx (Tarla harita bileşeni; → geometry.py)
        │   │   ├── map/
        │   │   │   ├── FieldMap.tsx (Genel harita bileşeni; re-export → field/FieldMap.tsx)
        │   │   │   └── MapLayerViewer.tsx (Harita katman kontrol; opacity/visibility)
        │   │   ├── mission/
        │   │   │   ├── MissionList.tsx (Görev listesi bileşeni; → useMissions.ts)
        │   │   │   └── MissionTimeline.tsx (Görev zaman çizelgesi; → useMissions.ts)
        │   │   ├── payment/
        │   │   │   ├── DekontViewer.tsx (KR-033 dekont görüntüleyici; → PaymentStatusBadge.tsx)
        │   │   │   ├── IbanInstructions.tsx (KR-033 IBAN talimat ekranı; kopyala + yükle)
        │   │   │   ├── PaymentStatusBadge.tsx (KR-033 ödeme durum badge; 5 durum)
        │   │   │   └── PaymentUpload.tsx (Dekont yükleme bileşeni; → useUpload.ts)
        │   │   ├── result/
        │   │   │   ├── ResultDetailPanel.tsx (Sonuç detay paneli; metrikler)
        │   │   │   └── ResultGallery.tsx (Sonuç galeri görünümü)
        │   │   ├── results/
        │   │   │   ├── LayerList.tsx (Analiz katman listesi; re-export → features/results/)
        │   │   │   └── MetricsDashboard.tsx (Sonuç metrikleri dashboard)
        │   │   └── subscription/
        │   │       ├── CreateSubscriptionFlow.tsx (KR-027 abonelik oluşturma akışı)
        │   │       ├── PlanCards.tsx (Abonelik plan kartları)
        │   │       └── SubscriptionTable.tsx (Abonelik tablosu)
        │   ├── layout/           (Sayfa düzeni bileşenleri)
        │   │   ├── AppShell.tsx  (Ana uygulama kabuğu; sidebar + content)
        │   │   ├── SideNav.tsx   (Sol navigasyon menüsü; rol bazlı)
        │   │   └── TopNav.tsx    (Üst navigasyon çubuğu; kullanıcı bilgisi)
        │   └── ui/               (Primitif UI bileşenleri — tasarım sistemi)
        │       ├── badge.tsx     (Badge bileşeni)
        │       ├── button.tsx    (Button bileşeni)
        │       ├── card.tsx      (Card bileşeni)
        │       ├── input.tsx     (Input bileşeni)
        │       ├── modal.tsx     (Modal dialog bileşeni)
        │       ├── select.tsx    (Select bileşeni)
        │       └── toast.tsx     (Toast bileşeni; re-export → ToastProvider.tsx)
        ├── features/             (Alan bazlı modüller — hooks, services, components)
        │   ├── expert-portal/    (KR-019 uzman portal modülü)
        │   │   ├── types.ts      (Uzman portal TypeScript tipleri)
        │   │   ├── components/
        │   │   │   ├── ExpertNotificationBell.tsx (Uzman bildirim zili; → useExpertNotifications.ts)
        │   │   │   ├── ImageViewer.tsx (Analiz görüntü görüntüleyici)
        │   │   │   ├── ReviewCard.tsx (İnceleme kartı bileşeni)
        │   │   │   ├── VerdictForm.tsx (Uzman karar formu; confirmed|corrected|rejected)
        │   │   │   ├── WorkQueueStats.tsx (İş kuyruğu istatistikleri)
        │   │   │   └── WorkQueueTable.tsx (İş kuyruğu tablosu)
        │   │   ├── hooks/
        │   │   │   ├── useExpertNotifications.ts (Uzman WebSocket bildirimleri; → notification_manager.py)
        │   │   │   ├── useExpertQueue.ts (Uzman iş kuyruğu hook; → expertReviewService.ts)
        │   │   │   ├── useExpertReview.ts (Tekil inceleme hook; → expertReviewService.ts)
        │   │   │   └── useExpertReviews.ts (İnceleme listesi hook; → expertReviewService.ts)
        │   │   └── services/
        │   │       └── expertReviewService.ts (Uzman inceleme API istemcisi; → expert_portal.py)
        │   ├── results/          (Analiz sonuç modülü)
        │   │   ├── components/
        │   │   │   ├── LayerList.tsx (Analiz katman listesi; → resultService.ts)
        │   │   │   └── MapLayerViewer.tsx (Sonuç harita katman görüntüleyici; → resultService.ts)
        │   │   ├── hooks/
        │   │   │   └── useResults.ts (Sonuç veri hook; → resultService.ts)
        │   │   └── services/
        │   │       └── resultService.ts (Sonuç API istemcisi; → results.py)
        │   ├── subscriptions/    (Abonelik modülü)
        │   │   ├── components/
        │   │   │   ├── MissionScheduleCalendar.tsx (Görev takvim bileşeni)
        │   │   │   ├── SubscriptionCard.tsx (Abonelik kartı bileşeni)
        │   │   │   └── SubscriptionPlanSelector.tsx (Plan seçici bileşeni)
        │   │   ├── hooks/
        │   │   │   └── useSubscriptions.ts (Abonelik veri hook; → subscriptionService.ts)
        │   │   └── services/
        │   │       └── subscriptionService.ts (Abonelik API istemcisi; → subscriptions.py)
        │   ├── training-feedback/ (KR-029 eğitim geri bildirim modülü)
        │   │   ├── components/
        │   │   │   └── FeedbackQualityIndicator.tsx (Geri bildirim kalite göstergesi)
        │   │   └── services/
        │   │       └── trainingFeedbackService.ts (Eğitim feedback API istemcisi; → training_feedback.py)
        │   └── weather-block/    (KR-015-3A hava engeli modülü)
        │       ├── components/
        │       │   └── WeatherBlockReportCard.tsx (Hava engeli rapor kartı)
        │       └── services/
        │           └── weatherBlockService.ts (Hava engeli API istemcisi; → weather_blocks.py)
        ├── hooks/                (Genel React hook'ları)
        │   ├── useAdminExperts.ts (Admin uzman yönetim hook; curated onboarding)
        │   ├── useAdminPayments.ts (KR-033 admin ödeme yönetim hook)
        │   ├── useAuditLogs.ts   (Denetim günlüğü sorgulama hook)
        │   ├── useAuth.ts        (KR-033 auth artefact lifecycle; → authStorage.ts)
        │   ├── useCorrelationId.ts (KR-071 correlation ID üretimi; → correlation.ts)
        │   ├── useDebounce.ts    (Debounce yardımcı hook)
        │   ├── useExpertQueue.ts (Re-export; → features/expert-portal/hooks/)
        │   ├── useExpertReview.ts (Re-export; → features/expert-portal/hooks/)
        │   ├── useFeatureFlags.ts (Feature flag yönetim hook)
        │   ├── useFields.ts      (KR-013 tarla CRUD hook; → apiClient.ts)
        │   ├── useMissions.ts    (KR-028 görev listesi hook; → apiClient.ts)
        │   ├── useOfflineQueue.ts (Offline kuyruk hook; PWA sync)
        │   ├── usePagination.ts  (Sayfalama yardımcı hook)
        │   ├── usePilotCapacity.ts (KR-015-1 pilot kapasite hook; → apiClient.ts)
        │   ├── usePricing.ts     (KR-022 fiyat sorgulama hook; → apiClient.ts)
        │   ├── useQueryState.ts  (URL query state yönetim hook)
        │   ├── useResults.ts     (Re-export; → features/results/hooks/)
        │   ├── useRoleGuard.ts   (KR-063 rol bazlı erişim kontrolü hook)
        │   ├── useSWRConfig.ts   (SWR cache yapılandırma hook)
        │   ├── useSubscriptions.ts (Re-export; → features/subscriptions/hooks/)
        │   ├── useToast.ts       (Toast bildirim hook; → ToastProvider.tsx)
        │   ├── useUpload.ts      (Dosya yükleme hook; → apiClient.ts)
        │   └── useWeatherBlock.ts (KR-015-3A hava engeli hook; → apiClient.ts)
        ├── i18n/                 (Çoklu dil desteği)
        │   ├── ar.json           (Arapça çeviriler)
        │   ├── ku.json           (Kürtçe çeviriler)
        │   └── tr.ts             (Türkçe çeviriler — ana dil)
        ├── lib/                  (Yardımcı kütüphaneler)
        │   ├── apiClient.ts      (KR-071/KR-081 typed API istemcisi; corr ID header)
        │   ├── authStorage.ts    (KR-033 auth token saklama; TTL + temizleme)
        │   ├── constants.ts      (Sabit değerler; → routes.ts)
        │   ├── correlation.ts    (KR-071 correlation/request ID üretimi)
        │   ├── date.ts           (Tarih biçimlendirme yardımcıları; tr-TR locale)
        │   ├── env.ts            (Ortam değişkeni tip tanımları)
        │   ├── format-utils.ts   (Biçimlendirme: telefon, tarih, para, alan)
        │   ├── http.ts           (HTTP istemci yardımcısı; → correlation.ts)
        │   ├── logger.ts         (İstemci tarafı loglama; debug/info/warn/error)
        │   ├── money.ts          (Para birimi biçimlendirme; TRY kuruş)
        │   ├── paths.ts          (Dinamik route yardımcıları; → routes.ts)
        │   ├── performance.ts    (Web Vitals izleme; LCP, FID, CLS, TTFB)
        │   ├── queryKeys.ts      (React Query cache anahtar tanımları)
        │   ├── routes.ts         (KR-062 kanonik route tanımları; middleware import eder)
        │   ├── storage.ts        (localStorage soyutlama katmanı)
        │   ├── telemetry.ts      (KR-071 observability event izleme; corr ID)
        │   ├── validation-schemas.ts (KR-081 contract-first Zod şemaları; KR-050 telefon+PIN)
        │   ├── validation.ts     (KR-081 doğrulama yardımcıları)
        │   ├── zodSchemas.ts     (Zod şema parse yardımcıları)
        │   └── websocket/
        │       └── expertNotificationClient.ts (Uzman WebSocket bildirim istemcisi; → notification_manager.py)
        └── styles/
            └── globals.css       (Global CSS; Tailwind direktifleri)
```
