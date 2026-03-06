# PATH: src/core/ports/repositories/user_repository.py
# DESC: UserRepository portu.
# SSOT: KR-050 (kimlik), KR-063 (RBAC roller)
"""
UserRepository abstract port.

Sorumluluk: Core'un dış dünya ile temas ettiği interface'i tanımlar.
  User entity'sinin kalıcı depolama erişimini soyutlar.
  Kullanıcı oluşturma, güncelleme, kimlik doğrulama sorguları ve rol yönetimi.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (user_id, phone_number, role vb.).
  Çıktı: IO sonuçları (DB kayıt, Optional[User]).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; secret'lar env/secret manager; dış çağrılarda timeouts + TLS.
  PII redaction: pin_hash asla log'a yazılmaz; phone_number PII olarak maskelenir.
  KR-050: Telefon + PIN kimlik doğrulama.
  KR-066: PII ayrı tutulur.

Hata Modları (idempotency/retry/rate limit):
  Timeout, transient failure, idempotency; retry (exponential backoff)
  ve circuit breaker (opsiyonel).

Observability (log fields/metrics/traces):
  latency, error_code, retries; DB query time.

Testler: Contract test (port), integration test (DB/external stub), e2e (kritik akış).
Bağımlılıklar: Standart kütüphane + domain tipleri.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon (_impl) taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.core.domain.entities.user import User, UserRole


class UserRepository(ABC):
    """User persistence port (KR-050, KR-063).

    Kullanıcıların kalıcı depolama erişimini soyutlar.
    Infrastructure katmanı bu interface'i implemente eder.

    KR-050: Telefon + PIN kimlik doğrulama.
    KR-063: RBAC roller.
    Idempotency: user_id ve phone_number benzersizliği ile çift kayıt önlenir.
    """

    # ------------------------------------------------------------------
    # Kaydetme
    # ------------------------------------------------------------------
    @abstractmethod
    async def save(self, user: User) -> None:
        """User kaydet (insert veya update).

        Args:
            user: Kaydedilecek User entity'si.

        Raises:
            IntegrityError: user_id veya phone_number benzersizlik ihlali.
        """

    # ------------------------------------------------------------------
    # Tekil sorgular
    # ------------------------------------------------------------------
    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """user_id ile User getir.

        Args:
            user_id: Aranacak kullanıcı ID'si.

        Returns:
            User veya bulunamazsa None.
        """

    @abstractmethod
    async def find_by_phone_number(self, phone_number: str) -> Optional[User]:
        """phone_number ile User getir (KR-050 kimlik doğrulama).

        Giriş akışında telefon numarasıyla kullanıcı arama için kullanılır.

        Args:
            phone_number: Aranacak telefon numarası.

        Returns:
            User veya bulunamazsa None.
        """

    # ------------------------------------------------------------------
    # Liste sorguları
    # ------------------------------------------------------------------
    @abstractmethod
    async def list_by_role(self, role: UserRole) -> List[User]:
        """Belirli roldeki tüm kullanıcıları getir.

        Admin paneli ve rol bazlı raporlama için kullanılır.

        Args:
            role: Kullanıcı rolü (KR-063 kanonik roller).

        Returns:
            User listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_province(self, province: str) -> List[User]:
        """Belirli ildeki tüm kullanıcıları getir.

        Args:
            province: İl kodu/adı.

        Returns:
            User listesi (boş olabilir).
        """

    @abstractmethod
    async def list_by_coop_id(self, coop_id: uuid.UUID) -> List[User]:
        """Bir kooperatife bağlı tüm kullanıcıları getir (KR-014).

        Args:
            coop_id: Kooperatif ID'si.

        Returns:
            User listesi (boş olabilir).
        """

    # ------------------------------------------------------------------
    # Silme
    # ------------------------------------------------------------------
    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> None:
        """User sil.

        Args:
            user_id: Silinecek kullanıcı ID'si.

        Raises:
            KeyError: user_id bulunamadığında.
        """
