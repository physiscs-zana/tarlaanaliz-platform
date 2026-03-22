# BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated.
# KR-019: Expert review bildirim servisi (SMS + in-app).
"""Expert notification service — review atandığında SMS + websocket bildirimi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SmsGateway(Protocol):
    """SMS gönderim portu (provider-agnostic)."""

    def send(self, to_phone: str, message: str) -> None: ...


class WebsocketNotifier(Protocol):
    """WebSocket bildirim portu."""

    def notify(self, user_id: str, event: str, payload: dict[str, Any]) -> None: ...


@dataclass
class ExpertNotificationService:
    """KR-019: Uzman bildirim servisi — review atama ve SLA uyarıları."""

    sms_gateway: SmsGateway | None = None
    websocket_notifier: WebsocketNotifier | None = None

    def notify_review_assigned(self, expert_user_id: str, phone: str, review_id: str, mission_id: str) -> None:
        """Review atandığında uzmanı bilgilendir (SMS + WebSocket)."""
        msg = f"Yeni inceleme atandi: Gorev #{mission_id[:8]}. Lutfen Expert Portal'dan inceleyin."
        if self.sms_gateway:
            self.sms_gateway.send(phone, msg)
        if self.websocket_notifier:
            self.websocket_notifier.notify(
                expert_user_id,
                "EXPERT_REVIEW_ASSIGNED",
                {"review_id": review_id, "mission_id": mission_id},
            )

    def notify_sla_warning(self, expert_user_id: str, phone: str, review_id: str, hours_remaining: float) -> None:
        """SLA riski uyarısı — 4 saatlik SLA'nın son 1 saatinde."""
        msg = f"SLA uyarisi: Inceleme #{review_id[:8]} icin {hours_remaining:.0f} saat kaldi."
        if self.sms_gateway:
            self.sms_gateway.send(phone, msg)
        if self.websocket_notifier:
            self.websocket_notifier.notify(
                expert_user_id,
                "EXPERT_SLA_WARNING",
                {"review_id": review_id, "hours_remaining": hours_remaining},
            )
