"""
Notify User Use Case - Real-time notifications
"""
import uuid
from datetime import datetime, timedelta
from typing import Protocol, Dict, Any
from src.Entities import Notification, Report, User, NotificationType

class NotificationRepositoryProtocol(Protocol):
    async def save(self, notification: Notification) -> Notification: ...

class WebSocketGatewayProtocol(Protocol):
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> None: ...

class NotifyUserUseCase:
    """
    Business Logic: Create and send real-time notifications

    Business Rules:
    - Each notification stored in database
    - Real-time delivery via WebSocket
    - Auto-expire after 30 days
    - Different message templates per notification type
    """

    def __init__(
        self,
        notification_repository: NotificationRepositoryProtocol,
        websocket_gateway: WebSocketGatewayProtocol
    ):
        self.repository = notification_repository
        self.websocket = websocket_gateway

    async def notify_report_approved(self, report: Report) -> None:
        """Notify entity user that report was approved"""

        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=report.submitted_by,
            report_id=report.id,
            type=NotificationType.REPORT_APPROVED,
            title="Raport zatwierdzony",
            message=f"Twój raport {report.file_name} został zatwierdzony przez UKNF",
            context={
                "entity_name": report.entity_name,
                "report_type": report.report_type,
                "approved_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
                "comment": report.decision_comment
            },
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        # Save notification
        await self.repository.save(notification)

        # Send real-time WebSocket message
        await self._send_websocket_notification(notification)

    async def notify_report_rejected(self, report: Report, reason: str) -> None:
        """Notify entity user that report was rejected"""

        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=report.submitted_by,
            report_id=report.id,
            type=NotificationType.REPORT_REJECTED,
            title="Raport odrzucony",
            message=f"Twój raport {report.file_name} został odrzucony przez UKNF",
            context={
                "entity_name": report.entity_name,
                "report_type": report.report_type,
                "rejected_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
                "reason": reason
            },
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        # Save notification
        await self.repository.save(notification)

        # Send real-time WebSocket message
        await self._send_websocket_notification(notification)

    async def notify_report_submitted(self, report: Report) -> None:
        """Notify UKNF supervisors about new report submission"""

        # For now, we'll broadcast to all UKNF supervisors
        # In production, this would query user repository for UKNF users
        uknf_supervisors = ["uknf-supervisor-1", "uknf-supervisor-2"]  # Mock IDs

        for supervisor_id in uknf_supervisors:
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=supervisor_id,
                report_id=report.id,
                type=NotificationType.REPORT_SUBMITTED,
                title="Nowy raport do przeglądu",
                message=f"Nowy raport od {report.entity_name}: {report.file_name}",
                context={
                    "entity_name": report.entity_name,
                    "report_type": report.report_type,
                    "risk_score": report.risk_score,
                    "risk_level": report.risk_level,
                    "submitted_at": report.submitted_at.isoformat()
                },
                expires_at=datetime.utcnow() + timedelta(days=7)  # Shorter expiry
            )

            # Save notification
            await self.repository.save(notification)

            # Send real-time WebSocket message
            await self._send_websocket_notification(notification)

    async def _send_websocket_notification(self, notification: Notification) -> None:
        """Send WebSocket notification to user"""
        try:
            message = {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "notification_type": notification.type,
                    "created_at": notification.created_at.isoformat(),
                    "context": notification.context
                }
            }

            await self.websocket.send_to_user(notification.user_id, message)
        except Exception:
            # Don't fail notification if WebSocket fails
            pass
