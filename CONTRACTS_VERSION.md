# Contracts Version — Surum Sabitleme (Pinning)

> **KR-081** Contract-First: Backend, Frontend ve Worker ayni API/Event semasini
> konustugunun garantisi bu dosya ile saglanir.

## Aktif Contract Surumu

| Alan | Deger |
|------|-------|
| **Contract Set Version** | `1.1.0` |
| **Schema Draft** | JSON Schema draft 2020-12 |
| **SSOT Referansi** | `docs/TARLAANALIZ_SSOT_v1_2_0.txt` — KR-081 |
| **Checksum Dosyasi** | `CONTRACTS_SHA256.txt` |
| **Son Guncelleme** | 2026-03-04 |

## Contract Listesi

| Contract | Schema ID | Surum | Durum | v1.1.0 Degisiklikler |
|----------|-----------|-------|-------|---------------------|
| AnalysisJob | `analysis_job.v1` | 1.1.0 | Aktif | +available_bands, +band_class |
| AnalysisResult | `analysis_result.v1` | 1.1.0 | Aktif | +report_tier, +band_class, +available_layers, +thermal_summary |
| AI Feedback | `ai.feedback.v1` | 1.0.0 | Aktif | — |
| Training Export (CLS) | `training.feedback.cls.v1` | 1.0.0 | Aktif | — |
| Training Export (GEO) | `training.feedback.geo.v1` | 1.0.0 | Aktif | — |
| DatasetIngestRequest | `dataset_ingest_request.v1` | 1.1.0 | Aktif | +available_bands (zorunlu) |
| DatasetIngestResponse | `dataset_ingest_response.v1` | 1.0.0 | Aktif | — |

## v1.1.0 Eklenen Alanlar (Backward-Compatible)

| Alan | Tip | Zorunlu | Aciklama | KR Referans |
|------|-----|---------|----------|-------------|
| `available_bands` | `string[]` | Evet (ingest) | intake_manifest band listesi | KR-018 v1.2.0 |
| `band_class` | `string` | Hayir | BASIC_4BAND \| EXTENDED_5BAND | KR-018/KR-082 |
| `report_tier` | `string` | Hayir | TEMEL \| GENISLETILMIS \| KAPSAMLI | KR-023 v1.2.0 |
| `available_layers` | `string[]` | Hayir | Uretilen katman kodlari | KR-064 |
| `available_indices` | `string[]` | Hayir | Hesaplanan indeks listesi | KR-018/KR-082 |
| `thermal_summary` | `object\|null` | Hayir | CWSI, canopy_temp, delta_t, irrigation_eff | KR-084 |

## Surumleme Kurali (SemVer)

- **v1.x**: Geriye uyumlu (backward compatible) eklemeler serbest (optional field eklenebilir)
- **v2.0**: Breaking change; bu dosya + `CONTRACTS_SHA256.txt` zorunlu guncellenir
- Breaking change tespit edildiginde CI pipeline merge'u engeller (KR-041)

## Uyumluluk Matrisi

| Servis | Minimum Contract Version | Notlar |
|--------|--------------------------|--------|
| Backend (Platform) | 1.0.0 | Uretici + tuketici; v1.1.0 alanlari opsiyonel |
| AI Worker | 1.0.0 | Tuketici (AnalysisJob) + uretici (AnalysisResult); v1.1.0 band_class/report_tier |
| Frontend (PWA) | 1.0.0 | Tuketici (AnalysisResult); v1.1.0 report_tier/thermal goruntuleme |
| Edge Kiosk | 1.1.0 | Uretici: available_bands zorunlu (v1.2.0 SSOT gereksinimi) |
