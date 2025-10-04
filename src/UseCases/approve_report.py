"""
Approve Report Use Case - UKNF business logic
"""
from datetime import datetime
from typing import Protocol
from src.Entities import Report, User, ReportStatus

class ReportRepositoryProtocol(Protocol):
    async def get_by_id(self, report_id: str) -> Report | None: ...
    async def save(self, report: Report) -> Report: ...

class NotificationGatewayProtocol(Protocol):
    async def notify_report_approved(self, report: Report) -> None: ...

class ApproveReportUseCase:
    """
    Business Logic: UKNF Supervisor approves report

    Business Rules:
    - Only UKNF supervisors can approve
    - Report must be in SUBMITTED status
    - Approval creates notification to entity user
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
        comment: str | None = None
    ) -> Report:
        """Execute report approval"""

        # Business Rule: Only UKNF can approve
        if not supervisor.is_uknf_user():
            raise ValueError("Only UKNF supervisors can approve reports")

        # Get report
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Business Rule: Can only approve submitted reports
        if report.status != ReportStatus.SUBMITTED:
            raise ValueError(f"Cannot approve report in status {report.status}")

        # Update report
        report.status = ReportStatus.APPROVED
        report.reviewed_at = datetime.utcnow()
        report.reviewed_by = supervisor.id
        report.decision_comment = comment

        # Save
        updated_report = await self.repository.save(report)

        # Notify entity user
        try:
            await self.notifier.notify_report_approved(updated_report)
        except Exception:
            pass  # Don't fail approval if notification fails

        return updated_report
