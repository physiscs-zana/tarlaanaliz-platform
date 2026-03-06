# PATH: src/infrastructure/contracts/schema_registry.py
# DESC: Contract şemalarını (JSON Schema) versiyonlu yükleyen ve cache'leyen bileşen.
"""
SchemaRegistry: versiyonlu JSON Schema yönetimi ve cache.

Domain event'leri ve DTO'lar için contract şemalarını yükler, doğrular
ve bellek içi cache'ler. Şemalar dosya sisteminden veya dict olarak
kaydedilebilir.

SSOT: tarlaanaliz_platform_tree v3.2.2 FINAL.
KR-081: contract-first tasarım; şema uyumsuzluğu erken tespit edilir.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class SchemaValidationError(Exception):
    """Şema doğrulama hatası."""


class SchemaNotFoundError(KeyError):
    """İstenen şema bulunamadı."""


class SchemaRegistry:
    """Versiyonlu JSON Schema kaydı (KR-081).

    Şemaları (schema_name, version) çifti ile indeksler.
    Bellek içi dict cache kullanır; thread-safe değildir
    (async context'te tek event loop yeterlidir).

    Kullanım:
        registry = SchemaRegistry()
        registry.register("MissionAssigned", "1.0.0", {...})
        schema = registry.get("MissionAssigned", "1.0.0")
        registry.load_directory(Path("schemas/"))
    """

    def __init__(self) -> None:
        self._schemas: dict[tuple[str, str], dict[str, Any]] = {}

    def register(
        self,
        schema_name: str,
        version: str,
        schema: dict[str, Any],
    ) -> None:
        """Şemayı kaydet veya güncelle.

        Args:
            schema_name: Şema adı (ör: "MissionAssigned").
            version: Semantik versiyon (ör: "1.0.0").
            schema: JSON Schema dict.

        Raises:
            ValueError: Geçersiz schema_name veya version.
        """
        if not schema_name or not schema_name.strip():
            raise ValueError("schema_name boş olamaz.")
        if not version or not version.strip():
            raise ValueError("version boş olamaz.")
        key = (schema_name.strip(), version.strip())
        self._schemas[key] = schema
        logger.debug(
            "schema_registered",
            schema_name=key[0],
            version=key[1],
        )

    def get(
        self,
        schema_name: str,
        version: str,
    ) -> dict[str, Any]:
        """Cache'ten şema döner.

        Args:
            schema_name: Şema adı.
            version: Semantik versiyon.

        Returns:
            JSON Schema dict.

        Raises:
            SchemaNotFoundError: Şema bulunamadığında.
        """
        key = (schema_name.strip(), version.strip())
        try:
            return self._schemas[key]
        except KeyError:
            raise SchemaNotFoundError(
                f"Şema bulunamadı: {key[0]} v{key[1]}. Kayıtlı şemalar: {sorted(self._schemas.keys())}"
            ) from None

    def has(self, schema_name: str, version: str) -> bool:
        """Şema mevcut mu?"""
        return (schema_name.strip(), version.strip()) in self._schemas

    def list_schemas(self) -> list[tuple[str, str]]:
        """Kayıtlı tüm (schema_name, version) çiftlerini döner."""
        return sorted(self._schemas.keys())

    def list_versions(self, schema_name: str) -> list[str]:
        """Belirli bir şemanın tüm versiyonlarını döner."""
        return sorted(version for name, version in self._schemas if name == schema_name.strip())

    def load_from_file(self, file_path: Path) -> tuple[str, str]:
        """Tek bir JSON Schema dosyasını yükler.

        Dosya adı formatı: <schema_name>.<version>.json
        Örnek: MissionAssigned.1.0.0.json

        Args:
            file_path: Şema dosyasının yolu.

        Returns:
            (schema_name, version) tuple.

        Raises:
            ValueError: Dosya adı formatı geçersizse.
            FileNotFoundError: Dosya bulunamazsa.
            json.JSONDecodeError: Geçersiz JSON.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Şema dosyası bulunamadı: {file_path}")

        parts = file_path.stem.rsplit(".", maxsplit=1)
        if len(parts) < 2:
            raise ValueError(
                f"Dosya adı formatı geçersiz: '{file_path.name}'. Beklenen format: <schema_name>.<version>.json"
            )

        schema_name = parts[0]
        version = parts[1]

        content = file_path.read_text(encoding="utf-8")
        schema = json.loads(content)
        self.register(schema_name, version, schema)

        return (schema_name, version)

    def load_directory(self, directory: Path) -> int:
        """Dizindeki tüm .json şema dosyalarını yükler.

        Args:
            directory: Şema dosyalarının bulunduğu dizin.

        Returns:
            Yüklenen şema sayısı.

        Raises:
            FileNotFoundError: Dizin bulunamazsa.
        """
        if not directory.exists():
            raise FileNotFoundError(f"Şema dizini bulunamadı: {directory}")

        count = 0
        for file_path in sorted(directory.glob("*.json")):
            try:
                self.load_from_file(file_path)
                count += 1
            except (ValueError, json.JSONDecodeError) as exc:
                logger.warning(
                    "schema_load_skipped",
                    file=str(file_path),
                    error=str(exc),
                )

        logger.info("schema_directory_loaded", directory=str(directory), count=count)
        return count

    def clear(self) -> None:
        """Tüm cache'lenmiş şemaları temizler."""
        self._schemas.clear()
