"""
Reject Report Use Case - UKNF business logic
"""
from datetime import datetime
from typing import Protocol
from src.Entities import Report, User, ReportStatus

class ReportRepositoryProtocol(Protocol):
    async def get_by_id(self, report_id: str) -> Report | None: ...
    async def save(self, report: Report) -> Report: ...

class NotificationGatewayProtocol(Protocol):
    async def notify_report_rejected(self, report: Report, reason: str) -> None: ...

class RejectReportUseCase:
    """
    Business Logic: UKNF Supervisor rejects report

    Business Rules:
    - Only UKNF supervisors can reject
    - Rejection comment is mandatory
    - Creates notification with feedback for entity
    """

    def __init__(
        self,
        report_repository: ReportRepositoryProtocol,
        notification_gateway: NotificationGatewayProtocol
    ):
        self.repository = report_repository
        self.notifier = notification_gateway

    async def execute(
        self,
        supervisor: User,
        report_id: str,
        comment: str
    ) -> Report:
        """Execute report rejection"""

        # Business Rule: Only UKNF can reject
        if not supervisor.is_uknf_user():
            raise ValueError("Only UKNF supervisors can reject reports")

        # Business Rule: Comment mandatory for rejections
        if not comment or comment.strip() == "":
            raise ValueError("Rejection comment is required")

        # Get report
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Business Rule: Can only reject submitted reports
        if report.status != ReportStatus.SUBMITTED:
            raise ValueError(f"Cannot reject report in status {report.status}")

        # Update report
        report.status = ReportStatus.REJECTED
        report.reviewed_at = datetime.utcnow()
        report.reviewed_by = supervisor.id
        report.decision_comment = comment.strip()

        # Save
        updated_report = await self.repository.save(report)

        # Notify entity user with feedback
        try:
            await self.notifier.notify_report_rejected(updated_report, comment)
        except Exception:
            pass  # Don't fail rejection if notification fails

        return updated_report
