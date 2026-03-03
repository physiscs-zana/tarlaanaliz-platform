# TarlaAnaliz Platform — Dizin Yapısı (Tree)

> **Bu dosyanın konumu:** `tarlaanaliz-platform_/DIRECTORY_TREE.md`
> **Son güncelleme:** 2026-03-03

```
tarlaanaliz-platform/
├── .dockerignore
├── .env.example
├── .gitattributes
├── .gitignore
├── .gitmodules
├── .pre-commit-config.yaml
├── AGENTS.md
├── CHANGELOG.md
├── CONTRACTS_SHA256.txt
├── CONTRACTS_VERSION.md
├── DIRECTORY_TREE.md                ← bu dosya
├── Dockerfile
├── MANIFEST_CANONICAL.md
├── PRODUCTION_READINESS_REPORT.md
├── README.md
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
│
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml
│       ├── contract_validation.yml
│       ├── deploy-staging.yml
│       ├── frontend-ci.yml
│       └── security.yml
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 20260101_001_initial_users_roles.py
│       ├── 20260101_002_initial_fields_crops.py
│       ├── 20260101_003_initial_missions.py
│       ├── 20260102_004_subscriptions.py
│       ├── 20260102_005_pilots.py
│       ├── 20260102_006_experts.py
│       ├── 20260103_007_analysis_jobs.py
│       ├── 20260103_008_expert_reviews.py
│       ├── 20260104_009_weather_blocks.py
│       ├── 20260104_010_audit_logs.py
│       ├── 20260104_011_weekly_schedules.py
│       ├── 20260105_012_indexes_performance.py
│       ├── 20260105_013_full_text_search.py
│       ├── 20260129_kr033_payment_intents.py
│       ├── 20260201_kr082_calibration_qc_records.py
│       ├── 20260204_add_weather_block_reports.py
│       ├── 20260223_kr015c_mission_schedule_fields.py
│       ├── 20260225_014_kr015_mission_segments.py
│       ├── 20260225_015_kr015_seasonal_reschedule_tokens.py
│       ├── 20260302_add_billing_admin_role.py
│       └── 20260302_simplify_weather_block_status.py
│
├── config/
│   ├── drone_registry.yaml
│   ├── logging.yaml
│   └── rate_limits/
│       ├── base_limits.yaml
│       └── seasonal_config.yaml
│
├── contracts/
│
├── deploy/
│   └── k8s/
│       ├── deployment.yaml
│       └── network-policy.yaml
│
├── docs/
│   ├── IS_PLANI_AKIS_DOKUMANI_v1_0_0.docx
│   ├── KR-033_payment_flow.md
│   ├── README.md
│   ├── TARLAANALIZ_SSOT_v1_0_0.txt
│   ├── is_plani_amendments.md
│   ├── v3_2_2_tree_audit_report.md
│   ├── adr/
│   │   └── ADR-001-nine-state-machine.md
│   ├── api/
│   │   ├── authentication.md
│   │   └── openapi.yaml
│   ├── architecture/
│   │   ├── adaptive_rate_limiting.md
│   │   ├── clean_architecture.md
│   │   ├── data_lifecycle_transfer.md
│   │   ├── event_driven_design.md
│   │   ├── expert_portal_design.md
│   │   ├── subscription_scheduler_design.md
│   │   ├── training_feedback_architecture.md
│   │   └── two_server_architecture.md
│   ├── archive/
│   │   └── 2026-02/
│   │       ├── GOVERNANCE_PACK_v1_0_0_2026-02-15.md
│   │       ├── IS_PLANI_AKIS_DOKUMANI_v1_0_0_OLD.docx
│   │       ├── IS_PLANI_AKIS_DOKUMANI_v1_0_0_UPDATED_2026-02-14.docx
│   │       ├── KR-033_payment_flow_OLD.md
│   │       ├── TARLAANALIZ_LLM_BRIEF_v1_0_0_OLD.md
│   │       ├── TARLAANALIZ_PLAYBOOK_v1_0_0_OLD.md
│   │       ├── TARLAANALIZ_SSOT_v1_0_0_DOCS_CLEAN_2026-02-14_v7.txt
│   │       ├── TARLAANALIZ_SSOT_v1_0_0_OLD.txt
│   │       ├── kr_registry_OPTIMAL_2026-02-14_v7.md
│   │       └── tarlaanaliz_platform_tree_v3.2.2_FINAL_2026-02-08_OLD.txt
│   ├── governance/
│   │   └── GOVERNANCE_PACK_v1_0_0.md
│   ├── kr/
│   │   └── kr_registry.md
│   ├── migration_guides/
│   │   └── README.md
│   ├── runbooks/
│   │   ├── expert_onboarding_procedure.md
│   │   ├── incident_response_payment_timeout.md
│   │   ├── incident_response_sla_breach.md
│   │   ├── payment_approval_procedure.md
│   │   └── weather_block_verification_procedure.md
│   ├── security/
│   │   ├── ddos_mitigation_plan.md
│   │   └── model_protection_strategy.md
│   └── views/
│       ├── VIEW_3D_GROUPING.md
│       ├── VIEW_CAPABILITIES.md
│       └── VIEW_SDLC.md
│
├── scripts/
│   ├── analyze_rate_limit_logs.py
│   ├── audit_v322_tree.py
│   ├── backup_database.sh
│   ├── check_ssot_compliance.py
│   ├── export_training_dataset.py
│   ├── generate_openapi.py
│   ├── seed_data.py
│   └── seed_experts.py
│
├── src/
│   ├── __init__.py
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── approve_payment.py
│   │   │   ├── assign_mission.py
│   │   │   ├── calculate_payroll.py
│   │   │   ├── create_field.py
│   │   │   ├── create_subscription.py
│   │   │   ├── register_expert.py
│   │   │   ├── report_weather_block.py
│   │   │   ├── schedule_mission.py
│   │   │   ├── submit_expert_review.py
│   │   │   ├── submit_training_feedback.py
│   │   │   ├── update_pilot_capacity.py
│   │   │   └── verify_weather_block.py
│   │   ├── dto/
│   │   │   ├── __init__.py
│   │   │   ├── analysis_result_dto.py
│   │   │   ├── expert_dashboard_dto.py
│   │   │   ├── expert_dto.py
│   │   │   ├── expert_review_dto.py
│   │   │   ├── field_dto.py
│   │   │   ├── mission_dto.py
│   │   │   ├── payment_intent_dto.py
│   │   │   ├── pilot_dto.py
│   │   │   ├── subscription_dto.py
│   │   │   ├── training_export_dto.py
│   │   │   ├── user_dto.py
│   │   │   └── weather_block_dto.py
│   │   ├── event_handlers/
│   │   │   ├── analysis_completed_handler.py
│   │   │   ├── expert_review_completed_handler.py
│   │   │   ├── mission_lifecycle_handler.py
│   │   │   └── subscription_created_handler.py
│   │   ├── jobs/
│   │   │   └── weekly_planning_job.py
│   │   ├── payments/
│   │   │   ├── dtos.py
│   │   │   └── service.py
│   │   ├── queries/
│   │   │   ├── __init__.py
│   │   │   ├── export_training_data.py
│   │   │   ├── get_active_price_plans.py
│   │   │   ├── get_expert_queue_stats.py
│   │   │   ├── get_expert_review_details.py
│   │   │   ├── get_field_details.py
│   │   │   ├── get_mission_timeline.py
│   │   │   ├── get_pilot_available_slots.py
│   │   │   ├── get_subscription_details.py
│   │   │   ├── list_pending_expert_reviews.py
│   │   │   ├── list_pilot_missions.py
│   │   │   └── lookup_parcel_geometry.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── audit_log_service.py
│   │   │   ├── calibration_gate_service.py
│   │   │   ├── contract_validator_service.py
│   │   │   ├── expert_review_service.py
│   │   │   ├── field_service.py
│   │   │   ├── mission_lifecycle_manager.py
│   │   │   ├── mission_service.py
│   │   │   ├── planning_capacity.py
│   │   │   ├── pricebook_service.py
│   │   │   ├── qc_gate_service.py
│   │   │   ├── reassignment_handler.py
│   │   │   ├── subscription_scheduler.py
│   │   │   ├── training_export_service.py
│   │   │   ├── training_feedback_service.py
│   │   │   ├── weather_block_service.py
│   │   │   └── weekly_window_scheduler.py
│   │   └── workers/
│   │       └── replan_queue_worker.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis_job.py
│   │   │   │   ├── analysis_result.py
│   │   │   │   ├── audit_log_entry.py
│   │   │   │   ├── calibration_record.py
│   │   │   │   ├── expert.py
│   │   │   │   ├── expert_review.py
│   │   │   │   ├── feedback_record.py
│   │   │   │   ├── field.py
│   │   │   │   ├── mission.py
│   │   │   │   ├── payment_intent.py
│   │   │   │   ├── pilot.py
│   │   │   │   ├── price_snapshot.py
│   │   │   │   ├── qc_report_record.py
│   │   │   │   ├── subscription.py
│   │   │   │   ├── user.py
│   │   │   │   ├── user_pii.py
│   │   │   │   └── weather_block_report.py
│   │   │   ├── events/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis_events.py
│   │   │   │   ├── base.py
│   │   │   │   ├── expert_events.py
│   │   │   │   ├── expert_review_events.py
│   │   │   │   ├── field_events.py
│   │   │   │   ├── mission_events.py
│   │   │   │   ├── payment_events.py
│   │   │   │   ├── subscription_events.py
│   │   │   │   └── training_feedback_events.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auto_dispatcher.py
│   │   │   │   ├── band_compliance_checker.py
│   │   │   │   ├── calibration_validator.py
│   │   │   │   ├── capacity_manager.py
│   │   │   │   ├── confidence_evaluator.py
│   │   │   │   ├── coverage_calculator.py
│   │   │   │   ├── expert_assignment_service.py
│   │   │   │   ├── mission_planner.py
│   │   │   │   ├── plan_window_segmenter.py
│   │   │   │   ├── planning_engine.py
│   │   │   │   ├── pricebook_calculator.py
│   │   │   │   ├── qc_evaluator.py
│   │   │   │   ├── reschedule_service.py
│   │   │   │   ├── sla_monitor.py
│   │   │   │   ├── subscription_planner.py
│   │   │   │   └── weather_validator.py
│   │   │   └── value_objects/
│   │   │       ├── __init__.py
│   │   │       ├── ai_confidence.py
│   │   │       ├── assignment_policy.py
│   │   │       ├── calibration_manifest.py
│   │   │       ├── confidence_score.py
│   │   │       ├── crop_ops_profile.py
│   │   │       ├── crop_type.py
│   │   │       ├── expert_specialization.py
│   │   │       ├── geometry.py
│   │   │       ├── mission_status.py
│   │   │       ├── money.py
│   │   │       ├── parcel_ref.py
│   │   │       ├── payment_status.py
│   │   │       ├── pilot_schedule.py
│   │   │       ├── price_snapshot.py
│   │   │       ├── province.py
│   │   │       ├── qc_flag.py
│   │   │       ├── qc_report.py
│   │   │       ├── qc_status.py
│   │   │       ├── recommended_action.py
│   │   │       ├── role.py
│   │   │       ├── sla_metrics.py
│   │   │       ├── sla_threshold.py
│   │   │       ├── specialization.py
│   │   │       ├── subscription_plan.py
│   │   │       ├── training_grade.py
│   │   │       └── weather_block_status.py
│   │   └── ports/
│   │       ├── __init__.py
│   │       ├── external/
│   │       │   ├── __init__.py
│   │       │   ├── ai_worker_feedback.py
│   │       │   ├── ddos_protection.py
│   │       │   ├── parcel_geometry_provider.py
│   │       │   ├── payment_gateway.py
│   │       │   ├── sms_gateway.py
│   │       │   └── storage_service.py
│   │       ├── messaging/
│   │       │   ├── __init__.py
│   │       │   └── event_bus.py
│   │       └── repositories/
│   │           ├── __init__.py
│   │           ├── analysis_result_repository.py
│   │           ├── audit_log_repository.py
│   │           ├── calibration_record_repository.py
│   │           ├── expert_repository.py
│   │           ├── expert_review_repository.py
│   │           ├── feedback_record_repository.py
│   │           ├── field_repository.py
│   │           ├── mission_repository.py
│   │           ├── payment_intent_repository.py
│   │           ├── pilot_repository.py
│   │           ├── price_snapshot_repository.py
│   │           ├── qc_report_repository.py
│   │           ├── subscription_repository.py
│   │           ├── user_repository.py
│   │           ├── weather_block_report_repository.py
│   │           └── weather_block_repository.py
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── contracts/
│   │   │   ├── __init__.py
│   │   │   └── schema_registry.py
│   │   ├── external/
│   │   │   ├── __init__.py
│   │   │   ├── av_scanner_client.py
│   │   │   ├── drone_registry_loader.py
│   │   │   ├── payment_gateway_adapter.py
│   │   │   ├── sms_gateway_adapter.py
│   │   │   ├── storage_adapter.py
│   │   │   ├── tkgm_megsis_wfs_adapter.py
│   │   │   └── weather_api_adapter.py
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── cloudflare/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ddos_protection.py
│   │   │   ├── payments/
│   │   │   │   ├── __init__.py
│   │   │   │   └── provider_gateway.py
│   │   │   ├── sms/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── netgsm.py
│   │   │   │   └── twilio.py
│   │   │   └── storage/
│   │   │       ├── __init__.py
│   │   │       └── s3_storage.py
│   │   ├── messaging/
│   │   │   ├── __init__.py
│   │   │   ├── event_publisher.py
│   │   │   ├── rabbitmq_config.py
│   │   │   ├── rabbitmq_event_bus_impl.py
│   │   │   ├── rabbitmq/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_feedback_publisher.py
│   │   │   │   ├── consumer.py
│   │   │   │   ├── publisher.py
│   │   │   │   └── training_feedback_publisher.py
│   │   │   └── websocket/
│   │   │       ├── __init__.py
│   │   │       └── notification_manager.py
│   │   ├── monitoring/
│   │   │   ├── __init__.py
│   │   │   ├── health_checks.py
│   │   │   ├── prometheus_metrics.py
│   │   │   └── security_events.py
│   │   ├── notifications/
│   │   │   └── pilot_notification_service.py
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── models/
│   │   │   │   ├── crop_ops_profile_model.py
│   │   │   │   ├── mission_segment_model.py
│   │   │   │   ├── payment_intent_model.py
│   │   │   │   ├── reschedule_request_model.py
│   │   │   │   └── weather_block_report_model.py
│   │   │   ├── redis/
│   │   │   │   ├── cache.py
│   │   │   │   └── rate_limiter.py
│   │   │   ├── repositories/
│   │   │   │   ├── mission_segment_repository.py
│   │   │   │   ├── payment_intent_repo.py
│   │   │   │   └── reschedule_repository.py
│   │   │   └── sqlalchemy/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── models.py
│   │   │       ├── session.py
│   │   │       ├── unit_of_work.py
│   │   │       ├── migrations/
│   │   │       │   └── versions/
│   │   │       │       ├── 2026_01_26_add_expert_portal_tables.py
│   │   │       │       ├── 2026_01_27_add_v2_6_0_tables.py
│   │   │       │       └── 2026_02_02_add_pricebook_tables.py
│   │   │       ├── models/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── analysis_job_model.py
│   │   │       │   ├── analysis_result_model.py
│   │   │       │   ├── audit_log_model.py
│   │   │       │   ├── expert_model.py
│   │   │       │   ├── expert_review_model.py
│   │   │       │   ├── field_model.py
│   │   │       │   ├── mission_model.py
│   │   │       │   ├── payment_intent_model.py
│   │   │       │   ├── pilot_model.py
│   │   │       │   ├── price_snapshot_model.py
│   │   │       │   ├── subscription_model.py
│   │   │       │   ├── user_model.py
│   │   │       │   └── weather_block_model.py
│   │   │       └── repositories/
│   │   │           ├── __init__.py
│   │   │           ├── analysis_result_repository_impl.py
│   │   │           ├── audit_log_repository_impl.py
│   │   │           ├── calibration_record_repository_impl.py
│   │   │           ├── crop_ops_profile_repository_impl.py
│   │   │           ├── expert_repository.py
│   │   │           ├── expert_repository_impl.py
│   │   │           ├── expert_review_repository.py
│   │   │           ├── expert_review_repository_impl.py
│   │   │           ├── feedback_record_repository.py
│   │   │           ├── feedback_record_repository_impl.py
│   │   │           ├── field_repository.py
│   │   │           ├── field_repository_impl.py
│   │   │           ├── mission_repository.py
│   │   │           ├── mission_repository_impl.py
│   │   │           ├── payment_intent_repository_impl.py
│   │   │           ├── pilot_repository_impl.py
│   │   │           ├── price_snapshot_repository_impl.py
│   │   │           ├── qc_report_repository_impl.py
│   │   │           ├── subscription_repository.py
│   │   │           ├── subscription_repository_impl.py
│   │   │           ├── user_repository_impl.py
│   │   │           ├── weather_block_report_repository_impl.py
│   │   │           └── weather_block_repository_impl.py
│   │   └── security/
│   │       ├── encryption.py
│   │       ├── jwt_handler.py
│   │       ├── query_pattern_analyzer.py
│   │       └── rate_limit_config.py
│   │
│   └── presentation/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dependencies.py
│       │   ├── main.py
│       │   ├── settings.py
│       │   ├── middleware/
│       │   │   ├── _shared.py
│       │   │   ├── anomaly_detection_middleware.py
│       │   │   ├── cors_middleware.py
│       │   │   ├── jwt_middleware.py
│       │   │   └── rate_limit_middleware.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── admin_payments.py
│       │       ├── calibration.py
│       │       ├── dependencies.py
│       │       ├── payments.py
│       │       ├── qc.py
│       │       ├── sla_metrics.py
│       │       ├── endpoints/
│       │       │   ├── __init__.py
│       │       │   ├── admin_audit.py
│       │       │   ├── admin_pricing.py
│       │       │   ├── auth.py
│       │       │   ├── expert_portal.py
│       │       │   ├── experts.py
│       │       │   ├── fields.py
│       │       │   ├── missions.py
│       │       │   ├── parcels.py
│       │       │   ├── payment_webhooks.py
│       │       │   ├── pilots.py
│       │       │   ├── pricing.py
│       │       │   ├── results.py
│       │       │   ├── subscriptions.py
│       │       │   ├── training_feedback.py
│       │       │   ├── weather_block_reports.py
│       │       │   └── weather_blocks.py
│       │       └── schemas/
│       │           ├── expert_review_schemas.py
│       │           ├── expert_schemas.py
│       │           ├── field_schemas.py
│       │           ├── mission_schemas.py
│       │           ├── parcel_schemas.py
│       │           ├── payment_webhook_schemas.py
│       │           ├── subscription_schemas.py
│       │           ├── training_feedback_schemas.py
│       │           └── weather_block_schemas.py
│       └── cli/
│           ├── __init__.py
│           ├── __main__.py
│           ├── main.py
│           └── commands/
│               ├── __init__.py
│               ├── expert_management.py
│               ├── migrate.py
│               ├── run_weekly_planner.py
│               ├── seed.py
│               └── subscription_management.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── e2e/
│   │   ├── __init__.py
│   │   ├── test_expert_journey.py
│   │   ├── test_farmer_journey.py
│   │   ├── test_payment_flow.py
│   │   └── test_pilot_journey.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── domain_fixtures.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api_calibration_qc.py
│   │   ├── test_api_fields.py
│   │   ├── test_api_payments_and_webhooks.py
│   │   ├── test_api_weather_block_reports.py
│   │   ├── test_event_bus.py
│   │   ├── test_field_repository.py
│   │   └── test_mission_repository.py
│   ├── performance/
│   │   ├── __init__.py
│   │   ├── locustfile.py
│   │   └── test_mission_assignment_load.py
│   ├── presentation/
│   │   ├── api/
│   │   │   ├── test_main.py
│   │   │   ├── test_v1_calibration_qc_sla.py
│   │   │   ├── test_v1_payments_admin.py
│   │   │   └── middleware/
│   │   │       ├── test_anomaly_detection_middleware.py
│   │   │       ├── test_cors_middleware.py
│   │   │       ├── test_jwt_middleware.py
│   │   │       └── test_rate_limit_middleware.py
│   │   └── cli/
│   │       └── test_cli_main.py
│   └── unit/
│       ├── __init__.py
│       ├── test_analysis_completed_handler.py
│       ├── test_calibration_gate.py
│       ├── test_payment_intent_dto.py
│       ├── test_payment_intent_manual_approval.py
│       ├── test_ssot_compliance_script.py
│       ├── test_weather_block_replan.py
│       ├── application/
│       │   ├── commands/
│       │   │   ├── test_assign_mission.py
│       │   │   └── test_create_field.py
│       │   └── services/
│       │       ├── test_application_services.py
│       │       └── test_payment_orchestration.py
│       ├── domain/
│       │   ├── entities/
│       │   │   ├── test_field.py
│       │   │   ├── test_mission.py
│       │   │   ├── test_payment_intent.py
│       │   │   └── test_subscription.py
│       │   ├── services/
│       │   │   ├── test_capacity_manager.py
│       │   │   └── test_planning_engine.py
│       │   └── value_objects/
│       │       ├── test_geometry.py
│       │       └── test_parcel_ref.py
│       └── infrastructure/
│           └── security/
│               └── test_security_stabilization.py
│
└── web/
    ├── README.md
    ├── eslint.config.mjs
    ├── jest.config.js
    ├── next.config.js
    ├── next.config.mjs
    ├── package.json
    ├── playwright.config.ts
    ├── pnpm-lock.yaml
    ├── postcss.config.mjs
    ├── sentry.client.config.ts
    ├── sentry.server.config.ts
    ├── tailwind.config.js
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── e2e/
    │   ├── admin-journey.spec.ts
    │   ├── expert-journey.spec.ts
    │   ├── farmer-journey.spec.ts
    │   ├── pilot-journey.spec.ts
    │   ├── playwright.config.ts
    │   └── tests/
    │       ├── auth.spec.ts
    │       ├── expert_journey.spec.ts
    │       └── farmer_journey.spec.ts
    ├── public/
    │   ├── manifest.json
    │   ├── robots.txt
    │   ├── service-worker.js
    │   ├── icons/
    │   │   ├── icon-192x192.png
    │   │   └── icon-512x512.png
    │   └── sounds/
    │       └── notification.mp3
    ├── scripts/
    │   └── ci/
    │       └── run.mjs
    └── src/
        ├── middleware.ts
        ├── app/
        │   ├── error.tsx
        │   ├── layout.tsx
        │   ├── loading.tsx
        │   ├── not-found.tsx
        │   ├── page.tsx
        │   ├── robots.ts
        │   ├── sitemap.ts
        │   ├── (admin)/
        │   │   ├── layout.tsx
        │   │   ├── loading.tsx
        │   │   ├── admin/
        │   │   │   ├── payments/
        │   │   │   │   └── page.tsx
        │   │   │   └── sla/
        │   │   │       └── page.tsx
        │   │   ├── analytics/
        │   │   │   └── page.tsx
        │   │   ├── api-keys/
        │   │   │   └── page.tsx
        │   │   ├── audit/
        │   │   ├── audit-viewer/
        │   │   │   └── page.tsx
        │   │   ├── calibration/
        │   │   │   └── page.tsx
        │   │   ├── dashboard/
        │   │   │   └── page.tsx
        │   │   ├── expert-management/
        │   │   │   └── page.tsx
        │   │   ├── experts/
        │   │   │   └── page.tsx
        │   │   ├── pilots/
        │   │   │   └── page.tsx
        │   │   ├── price-management/
        │   │   │   └── page.tsx
        │   │   ├── pricing/
        │   │   │   └── page.tsx
        │   │   ├── qc/
        │   │   │   └── page.tsx
        │   │   └── users/
        │   │       └── page.tsx
        │   ├── (auth)/
        │   │   ├── layout.tsx
        │   │   ├── login/
        │   │   │   └── page.tsx
        │   │   └── register/
        │   │       └── page.tsx
        │   ├── (expert)/
        │   │   ├── layout.tsx
        │   │   ├── expert/
        │   │   │   ├── profile/
        │   │   │   │   └── page.tsx
        │   │   │   ├── settings/
        │   │   │   │   └── page.tsx
        │   │   │   └── sla/
        │   │   │       └── page.tsx
        │   │   ├── queue/
        │   │   │   └── page.tsx
        │   │   ├── review/
        │   │   │   └── [reviewId]/
        │   │   │       └── page.tsx
        │   │   └── reviews/
        │   │       └── [id]/
        │   │           └── page.tsx
        │   ├── (farmer)/
        │   │   ├── layout.tsx
        │   │   ├── loading.tsx
        │   │   ├── fields/
        │   │   │   ├── page.tsx
        │   │   │   └── [id]/
        │   │   │       └── page.tsx
        │   │   ├── missions/
        │   │   │   ├── page.tsx
        │   │   │   └── [id]/
        │   │   │       └── page.tsx
        │   │   ├── payments/
        │   │   │   └── page.tsx
        │   │   ├── profile/
        │   │   │   └── page.tsx
        │   │   ├── results/
        │   │   │   ├── page.tsx
        │   │   │   └── [missionId]/
        │   │   │       └── page.tsx
        │   │   └── subscriptions/
        │   │       ├── page.tsx
        │   │       └── create/
        │   │           └── page.tsx
        │   ├── (pilot)/
        │   │   ├── layout.tsx
        │   │   ├── loading.tsx
        │   │   ├── capacity/
        │   │   │   └── page.tsx
        │   │   ├── pilot/
        │   │   │   ├── missions/
        │   │   │   │   └── page.tsx
        │   │   │   ├── profile/
        │   │   │   │   └── page.tsx
        │   │   │   └── settings/
        │   │   │       └── page.tsx
        │   │   ├── planner/
        │   │   │   └── page.tsx
        │   │   └── weather-block/
        │   │       └── page.tsx
        │   ├── admin/
        │   │   ├── experts/
        │   │   │   └── page.tsx
        │   │   ├── subscriptions/
        │   │   │   └── page.tsx
        │   │   └── weather-block/
        │   │       └── page.tsx
        │   ├── api/
        │   │   └── health/
        │   │       └── route.ts
        │   ├── expert/
        │   │   ├── layout.tsx
        │   │   ├── dashboard/
        │   │   │   └── page.tsx
        │   │   ├── history/
        │   │   │   └── page.tsx
        │   │   └── reviews/
        │   │       ├── page.tsx
        │   │       └── [id]/
        │   │           └── page.tsx
        │   ├── farmer/
        │   │   ├── missions/
        │   │   │   ├── page.tsx
        │   │   │   └── [id]/
        │   │   │       └── page.tsx
        │   │   ├── results/
        │   │   │   └── [missionId]/
        │   │   │       └── page.tsx
        │   │   └── subscriptions/
        │   │       └── page.tsx
        │   └── pilot/
        │       └── weather-block/
        │           └── page.tsx
        ├── components/
        │   ├── AccessibilityProvider.tsx
        │   ├── common/
        │   │   ├── AccessibilityProvider.tsx
        │   │   ├── ConfirmDialog.tsx
        │   │   ├── EmptyState.tsx
        │   │   ├── LoadingSpinner.tsx
        │   │   └── ToastProvider.tsx
        │   ├── features/
        │   │   ├── admin/
        │   │   │   ├── AuditLogTable.tsx
        │   │   │   └── SlaDashboard.tsx
        │   │   ├── dataset/
        │   │   │   └── DatasetUploadModal.tsx
        │   │   ├── expert/
        │   │   │   └── AnnotationCanvas.tsx
        │   │   ├── field/
        │   │   │   ├── AddFieldModal.tsx
        │   │   │   ├── FieldList.tsx
        │   │   │   └── FieldMap.tsx
        │   │   ├── map/
        │   │   │   ├── FieldMap.tsx
        │   │   │   └── MapLayerViewer.tsx
        │   │   ├── mission/
        │   │   │   ├── MissionList.tsx
        │   │   │   └── MissionTimeline.tsx
        │   │   ├── payment/
        │   │   │   ├── DekontViewer.tsx
        │   │   │   ├── PaymentStatusBadge.tsx
        │   │   │   └── PaymentUpload.tsx
        │   │   ├── result/
        │   │   │   ├── ResultDetailPanel.tsx
        │   │   │   └── ResultGallery.tsx
        │   │   ├── results/
        │   │   │   ├── LayerList.tsx
        │   │   │   └── MetricsDashboard.tsx
        │   │   └── subscription/
        │   │       ├── CreateSubscriptionFlow.tsx
        │   │       ├── PlanCards.tsx
        │   │       └── SubscriptionTable.tsx
        │   ├── layout/
        │   │   ├── AppShell.tsx
        │   │   ├── SideNav.tsx
        │   │   └── TopNav.tsx
        │   └── ui/
        │       ├── badge.tsx
        │       ├── button.tsx
        │       ├── card.tsx
        │       ├── input.tsx
        │       ├── modal.tsx
        │       ├── select.tsx
        │       └── toast.tsx
        ├── features/
        │   ├── expert-portal/
        │   │   ├── types.ts
        │   │   ├── components/
        │   │   │   ├── ExpertNotificationBell.tsx
        │   │   │   ├── ImageViewer.tsx
        │   │   │   ├── ReviewCard.tsx
        │   │   │   ├── VerdictForm.tsx
        │   │   │   ├── WorkQueueStats.tsx
        │   │   │   └── WorkQueueTable.tsx
        │   │   ├── hooks/
        │   │   │   ├── useExpertNotifications.ts
        │   │   │   ├── useExpertQueue.ts
        │   │   │   ├── useExpertReview.ts
        │   │   │   └── useExpertReviews.ts
        │   │   └── services/
        │   │       └── expertReviewService.ts
        │   ├── results/
        │   │   ├── components/
        │   │   │   ├── LayerList.tsx
        │   │   │   └── MapLayerViewer.tsx
        │   │   ├── hooks/
        │   │   │   └── useResults.ts
        │   │   └── services/
        │   │       └── resultService.ts
        │   ├── subscriptions/
        │   │   ├── components/
        │   │   │   ├── MissionScheduleCalendar.tsx
        │   │   │   ├── SubscriptionCard.tsx
        │   │   │   └── SubscriptionPlanSelector.tsx
        │   │   ├── hooks/
        │   │   │   └── useSubscriptions.ts
        │   │   └── services/
        │   │       └── subscriptionService.ts
        │   ├── training-feedback/
        │   │   ├── components/
        │   │   │   └── FeedbackQualityIndicator.tsx
        │   │   └── services/
        │   │       └── trainingFeedbackService.ts
        │   └── weather-block/
        │       ├── components/
        │       │   └── WeatherBlockReportCard.tsx
        │       └── services/
        │           └── weatherBlockService.ts
        ├── hooks/
        │   ├── useAdminExperts.ts
        │   ├── useAdminPayments.ts
        │   ├── useAuditLogs.ts
        │   ├── useAuth.ts
        │   ├── useCorrelationId.ts
        │   ├── useDebounce.ts
        │   ├── useExpertQueue.ts
        │   ├── useExpertReview.ts
        │   ├── useFeatureFlags.ts
        │   ├── useFields.ts
        │   ├── useMissions.ts
        │   ├── useOfflineQueue.ts
        │   ├── usePagination.ts
        │   ├── usePilotCapacity.ts
        │   ├── usePricing.ts
        │   ├── useQueryState.ts
        │   ├── useResults.ts
        │   ├── useRoleGuard.ts
        │   ├── useSWRConfig.ts
        │   ├── useSubscriptions.ts
        │   ├── useToast.ts
        │   ├── useUpload.ts
        │   └── useWeatherBlock.ts
        ├── i18n/
        │   ├── ar.json
        │   ├── ku.json
        │   ├── tr.json
        │   └── tr.ts
        ├── lib/
        │   ├── api-client.ts
        │   ├── apiClient.ts
        │   ├── authStorage.ts
        │   ├── constants.ts
        │   ├── correlation.ts
        │   ├── date.ts
        │   ├── env.ts
        │   ├── format-utils.ts
        │   ├── http.ts
        │   ├── logger.ts
        │   ├── money.ts
        │   ├── paths.ts
        │   ├── performance.ts
        │   ├── queryKeys.ts
        │   ├── routes.ts
        │   ├── storage.ts
        │   ├── telemetry.ts
        │   ├── validation-schemas.ts
        │   ├── validation.ts
        │   ├── zodSchemas.ts
        │   └── websocket/
        │       └── expertNotificationClient.ts
        └── styles/
            └── globals.css
```
