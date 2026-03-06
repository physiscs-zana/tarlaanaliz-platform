# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# PATH: src/infrastructure/external/drone_registry_loader.py
# DESC: Drone registry YAML yukleyici adapter (KR-030).
"""
Drone registry infrastructure adapter: config/drone_registry.yaml dosyasini yukler.

KR-030: Tum drone modelleri drone_registry.yaml'a kayitli olmalidir.
Kayitsiz drone modeli ile sistem baslatilmamali; kalibrasyon kalite zinciri
(KR-018 → KR-072) bu kaydina baglidir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml  # type: ignore[import-untyped]

from src.core.domain.value_objects.drone_model import DroneModel, DroneModelError

logger = structlog.get_logger(__name__)

DEFAULT_REGISTRY_PATH = Path("config/drone_registry.yaml")
DEFAULT_CAPABILITY_MATRIX_PATH = Path("config/drone_capability_matrix.yaml")


class DroneRegistryLoadError(Exception):
    """Registry yuklenirken hata."""


class DroneRegistryLoader:
    """Drone registry YAML dosyasini yukler ve DroneModel VO'larina donusturur.

    Infrastructure katmani adaptoru; domain katmani bu sinifi bilmez.
    Core portlar uzerinden erisim saglanir.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_REGISTRY_PATH
        self._models: dict[str, DroneModel] | None = None

    def _ensure_loaded(self) -> dict[str, DroneModel]:
        if self._models is not None:
            return self._models
        self._models = {}
        for model in self.load():
            self._models[model.model_id] = model
        return self._models

    def load(self) -> list[DroneModel]:
        """Registry dosyasini yukler ve tum modelleri dondurur.

        Returns:
            Yuklenen DroneModel listesi.

        Raises:
            DroneRegistryLoadError: Dosya bulunamaz veya parse edilemezse.
        """
        if not self._path.exists():
            raise DroneRegistryLoadError(f"Drone registry dosyasi bulunamadi: {self._path}")

        try:
            raw = yaml.safe_load(self._path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise DroneRegistryLoadError(f"YAML parse hatasi: {self._path}: {exc}") from exc

        if not isinstance(raw, dict) or "models" not in raw:
            raise DroneRegistryLoadError(f"Gecersiz registry formati: 'models' alani gerekli: {self._path}")

        models: list[DroneModel] = []
        for entry in raw["models"]:
            try:
                model = self._parse_entry(entry)
                models.append(model)
            except (DroneModelError, KeyError, TypeError) as exc:
                logger.warning(
                    "drone_registry.entry_skip",
                    entry_id=entry.get("id", "unknown"),
                    error=str(exc),
                )

        logger.info(
            "drone_registry.loaded",
            total_models=len(models),
            active_models=sum(1 for m in models if m.phase == 1),
            path=str(self._path),
        )
        return models

    def load_active_model_ids(self) -> frozenset[str]:
        """Yalnizca aktif (phase=1, status=active) model ID'lerini dondurur."""
        models = self._ensure_loaded()
        return frozenset(mid for mid, m in models.items() if m.phase == 1)

    def get_model(self, model_id: str) -> DroneModel | None:
        """Model ID'ye gore drone modelini dondurur."""
        models = self._ensure_loaded()
        return models.get(model_id)

    def list_models(self) -> list[DroneModel]:
        """Tum kayitli modelleri dondurur."""
        models = self._ensure_loaded()
        return list(models.values())

    def is_registered(self, model_id: str) -> bool:
        """Model ID'nin kayitli olup olmadigini kontrol eder."""
        models = self._ensure_loaded()
        return model_id in models

    def load_capability_matrix(
        self,
        path: Path | None = None,
    ) -> dict[str, Any]:
        """drone_capability_matrix.yaml dosyasini yukler.

        KR-018/KR-082: Spectral capability detection — drone bazli band sinifi,
        indeksler, termal sensor bilgisi ve graceful degradation yonlendirme tablosu.

        Returns:
            Parsed YAML icerigini dict olarak dondurur:
            - "capabilities": drone bazli kapasite listesi
            - "graceful_degradation": yonlendirme kurallari

        Raises:
            DroneRegistryLoadError: Dosya bulunamaz veya parse edilemezse.
        """
        matrix_path = path or DEFAULT_CAPABILITY_MATRIX_PATH
        if not matrix_path.exists():
            raise DroneRegistryLoadError(f"Capability matrix dosyasi bulunamadi: {matrix_path}")
        try:
            raw = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise DroneRegistryLoadError(f"YAML parse hatasi: {matrix_path}: {exc}") from exc

        if not isinstance(raw, dict) or "capabilities" not in raw:
            raise DroneRegistryLoadError(
                f"Gecersiz capability matrix formati: 'capabilities' alani gerekli: {matrix_path}"
            )

        logger.info(
            "drone_capability_matrix.loaded",
            version=raw.get("version", "unknown"),
            total_entries=len(raw["capabilities"]),
            path=str(matrix_path),
        )
        return raw

    @staticmethod
    def _parse_entry(entry: dict[str, Any]) -> DroneModel:
        """YAML entry'sini DroneModel VO'ya donusturur."""
        return DroneModel(
            model_id=entry["id"],
            manufacturer=entry["manufacturer"],
            model_name=entry["model"],
            sensor=entry["sensor"],
            bands=tuple(entry["bands"]),
            min_gsd_cm=float(entry["min_gsd_cm"]),
            radiometry_type=entry.get("radiometry_type", "relative"),
            phase=int(entry.get("phase", 1)),
            red_edge_wavelength_nm=float(entry.get("red_edge_wavelength_nm", 0.0)),
        )
