# PATH: src/infrastructure/messaging/websocket/notification_manager.py
# DESC: WebSocket bildirim yöneticisi (uzman portalı).
"""
WebSocket Notification Manager: uzman portalı için gerçek zamanlı bildirim yönetimi.

Amaç: WebSocket bağlantıları üzerinden uzman portalına gerçek zamanlı
  bildirimler göndermek. Domain event'lerini WebSocket mesajlarına
  dönüştürüp bağlı istemcilere push eder.

Sorumluluk: WebSocket bağlantı yönetimi, bildirim dispatch, bağlantı sağlığı.

Girdi/Çıktı (Contract/DTO/Event):
  Girdi: application/services çağrıları (bildirim gönderimi).
  Çıktı: WebSocket mesajları (JSON formatında bildirimler).

Güvenlik (RBAC/PII/Audit):
  En az ayrıcalık; WebSocket bağlantıları JWT ile doğrulanır.
  PII redaction: bildirim payload'larında PII minimizasyonu.
  Dış çağrılarda timeouts + TLS.

Hata Modları (idempotency/retry/rate limit):
  Bağlantı kopma, timeout; bağlantı yeniden kurma desteği.
  Rate limiting: istemci başına mesaj hızı sınırlaması.

Observability (log fields/metrics/traces):
  active_connections, messages_sent, errors, latency.

Testler: Contract test (port), integration test (WebSocket stub), e2e (kritik akış).
Bağımlılıklar: FastAPI WebSocket, structlog, asyncio.
Notlar/SSOT: Port interface core'da; infrastructure yalnızca implementasyon taşır.
  v3.2.2'de redundant çiftler kaldırıldı.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WebSocketConnection:
    """Tek bir WebSocket bağlantısının meta bilgisi."""

    connection_id: str
    user_id: str
    websocket: Any  # FastAPI WebSocket instance
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: Optional[datetime] = None


@dataclass(frozen=True)
class Notification:
    """Bildirim veri nesnesi (immutable)."""

    notification_id: str
    notification_type: str
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict dönüşümü."""
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }


class WebSocketNotificationManager:
    """WebSocket bildirim yöneticisi.

    Bağlı uzman portalı istemcilerine gerçek zamanlı bildirimler gönderir.
    Her kullanıcı birden fazla aktif bağlantıya sahip olabilir (birden
    fazla sekme/cihaz).

    Özellikler:
      - Kullanıcı bazlı bağlantı yönetimi
      - Broadcast (tüm kullanıcılara) ve unicast (tek kullanıcıya) bildirim
      - Periyodik ping/pong ile bağlantı sağlığı kontrolü
      - Otomatik dead connection temizleme
      - Bildirim geçmişi (bellek içi, son N bildirim)

    Kullanım:
        manager = WebSocketNotificationManager()
        await manager.connect(websocket, user_id)
        await manager.send_to_user(user_id, notification)
        await manager.disconnect(connection_id)
    """

    def __init__(
        self,
        *,
        max_history_size: int = 100,
        ping_interval_seconds: int = 30,
    ) -> None:
        # connection_id -> WebSocketConnection
        self._connections: dict[str, WebSocketConnection] = {}

        # user_id -> set[connection_id]
        self._user_connections: dict[str, set[str]] = {}

        # Bildirim geçmişi (son N)
        self._notification_history: list[Notification] = []
        self._max_history_size = max_history_size

        # Ping/pong ayarları
        self._ping_interval = ping_interval_seconds
        self._ping_task: Optional[asyncio.Task[None]] = None

    @property
    def active_connection_count(self) -> int:
        """Aktif bağlantı sayısı."""
        return len(self._connections)

    @property
    def active_user_count(self) -> int:
        """Aktif kullanıcı sayısı (en az bir bağlantısı olan)."""
        return len(self._user_connections)

    async def connect(
        self,
        websocket: Any,
        user_id: str,
    ) -> str:
        """Yeni WebSocket bağlantısı kaydet.

        Args:
            websocket: FastAPI WebSocket instance.
            user_id: Bağlanan kullanıcı ID'si.

        Returns:
            connection_id: Benzersiz bağlantı ID'si.
        """
        connection_id = f"ws-{uuid.uuid4().hex[:12]}"

        connection = WebSocketConnection(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
        )

        self._connections[connection_id] = connection

        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        logger.info(
            "websocket_connected",
            connection_id=connection_id,
            user_id=user_id,
            active_connections=self.active_connection_count,
        )

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """WebSocket bağlantısını kapat ve temizle.

        Args:
            connection_id: Kapatılacak bağlantı ID'si.
        """
        connection = self._connections.pop(connection_id, None)
        if connection is None:
            return

        user_id = connection.user_id

        # Kullanıcı bağlantı setinden kaldır
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(connection_id)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        logger.info(
            "websocket_disconnected",
            connection_id=connection_id,
            user_id=user_id,
            active_connections=self.active_connection_count,
        )

    async def send_to_user(
        self,
        user_id: str,
        notification: Notification,
    ) -> int:
        """Belirli bir kullanıcının tüm bağlantılarına bildirim gönder.

        Args:
            user_id: Hedef kullanıcı ID'si.
            notification: Gönderilecek bildirim.

        Returns:
            Başarıyla gönderilen bağlantı sayısı.
        """
        connection_ids = self._user_connections.get(user_id, set())
        if not connection_ids:
            logger.debug(
                "websocket_user_not_connected",
                user_id=user_id,
                notification_type=notification.notification_type,
            )
            return 0

        sent_count = 0
        failed_connections: list[str] = []
        payload = json.dumps(notification.to_dict(), default=str)

        for conn_id in list(connection_ids):
            connection = self._connections.get(conn_id)
            if connection is None:
                continue

            try:
                await connection.websocket.send_text(payload)
                sent_count += 1
            except Exception as exc:
                logger.warning(
                    "websocket_send_failed",
                    connection_id=conn_id,
                    user_id=user_id,
                    error=str(exc),
                )
                failed_connections.append(conn_id)

        # Başarısız bağlantıları temizle
        for conn_id in failed_connections:
            await self.disconnect(conn_id)

        # Geçmişe ekle
        self._add_to_history(notification)

        logger.info(
            "websocket_notification_sent",
            user_id=user_id,
            notification_type=notification.notification_type,
            sent_count=sent_count,
            failed_count=len(failed_connections),
        )

        return sent_count

    async def broadcast(
        self,
        notification: Notification,
        *,
        exclude_user_ids: Optional[set[str]] = None,
    ) -> int:
        """Tüm bağlı kullanıcılara bildirim gönder.

        Args:
            notification: Gönderilecek bildirim.
            exclude_user_ids: Hariç tutulacak kullanıcı ID'leri.

        Returns:
            Toplam gönderilen bağlantı sayısı.
        """
        start_time = time.monotonic()
        total_sent = 0
        exclude = exclude_user_ids or set()

        for user_id in list(self._user_connections.keys()):
            if user_id in exclude:
                continue
            sent = await self.send_to_user(user_id, notification)
            total_sent += sent

        latency_ms = (time.monotonic() - start_time) * 1000

        logger.info(
            "websocket_broadcast_completed",
            notification_type=notification.notification_type,
            total_sent=total_sent,
            user_count=self.active_user_count,
            latency_ms=round(latency_ms, 2),
        )

        return total_sent

    async def send_to_users(
        self,
        user_ids: list[str],
        notification: Notification,
    ) -> int:
        """Belirli kullanıcı grubuna bildirim gönder.

        Args:
            user_ids: Hedef kullanıcı ID listesi.
            notification: Gönderilecek bildirim.

        Returns:
            Toplam gönderilen bağlantı sayısı.
        """
        total_sent = 0
        for user_id in user_ids:
            sent = await self.send_to_user(user_id, notification)
            total_sent += sent
        return total_sent

    def is_user_connected(self, user_id: str) -> bool:
        """Kullanıcının aktif bağlantısı var mı?

        Args:
            user_id: Kontrol edilecek kullanıcı ID'si.

        Returns:
            True: Kullanıcı bağlı.
            False: Kullanıcı bağlı değil.
        """
        connections = self._user_connections.get(user_id, set())
        return len(connections) > 0

    def get_user_connection_count(self, user_id: str) -> int:
        """Kullanıcının aktif bağlantı sayısını döner."""
        return len(self._user_connections.get(user_id, set()))

    def _add_to_history(self, notification: Notification) -> None:
        """Bildirimi geçmişe ekle (boyut sınırlaması ile)."""
        self._notification_history.append(notification)
        if len(self._notification_history) > self._max_history_size:
            # En eski kayıtları kaldır
            overflow = len(self._notification_history) - self._max_history_size
            self._notification_history = self._notification_history[overflow:]

    def get_recent_notifications(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Son N bildirimi döner (en yeniden en eskiye).

        Args:
            limit: Döndürülecek bildirim sayısı.

        Returns:
            Bildirim dict listesi.
        """
        recent = self._notification_history[-limit:]
        recent.reverse()
        return [n.to_dict() for n in recent]

    async def start_ping_loop(self) -> None:
        """Periyodik ping/pong döngüsünü başlat.

        Dead connection'ları tespit edip temizler.
        """
        if self._ping_task is not None:
            return

        async def _ping_loop() -> None:
            while True:
                await asyncio.sleep(self._ping_interval)
                await self._ping_all_connections()

        self._ping_task = asyncio.create_task(_ping_loop())
        logger.info(
            "websocket_ping_loop_started",
            interval_seconds=self._ping_interval,
        )

    async def stop_ping_loop(self) -> None:
        """Ping/pong döngüsünü durdur."""
        if self._ping_task is not None:
            self._ping_task.cancel()
            self._ping_task = None
            logger.info("websocket_ping_loop_stopped")

    async def _ping_all_connections(self) -> None:
        """Tüm bağlantılara ping gönder, dead olanları temizle."""
        dead_connections: list[str] = []

        for conn_id, connection in list(self._connections.items()):
            try:
                await connection.websocket.send_json({"type": "ping"})
                connection.last_ping = datetime.now(timezone.utc)
            except Exception:
                dead_connections.append(conn_id)

        for conn_id in dead_connections:
            await self.disconnect(conn_id)

        if dead_connections:
            logger.info(
                "websocket_dead_connections_cleaned",
                count=len(dead_connections),
            )

    async def close_all(self) -> None:
        """Tüm bağlantıları kapat (graceful shutdown)."""
        await self.stop_ping_loop()

        for conn_id in list(self._connections.keys()):
            try:
                connection = self._connections.get(conn_id)
                if connection:
                    await connection.websocket.close()
            except Exception:
                pass
            await self.disconnect(conn_id)

        logger.info("websocket_all_connections_closed")
