"""
Get Reports Use Case - Role-based access control
"""
from typing import List, Optional, Protocol
from src.Entities import Report, User, ReportStatus

class ReportRepositoryProtocol(Protocol):
    async def get_by_entity_codes(
        self, 
        entity_codes: List[str],
        status: Optional[ReportStatus] = None,
        limit: Optional[int] = None
    ) -> List[Report]: ...

    async def get_all(
        self,
        status: Optional[ReportStatus] = None,
        limit: Optional[int] = None
    ) -> List[Report]: ...

class GetReportsUseCase:
    """
    Business Logic: Get reports with role-based filtering

    Business Rules:
    - Entity users: See only their entity reports
    - UKNF users: See all reports
    - Default sort: Recent first, then by risk score
    """

    def __init__(self, report_repository: ReportRepositoryProtocol):
        self.repository = report_repository

    async def execute(
        self,
        user: User,
        status: Optional[ReportStatus] = None,
        limit: Optional[int] = None
    ) -> List[Report]:
        """Get reports based on user access rights"""

        if user.is_uknf_user():
            # UKNF sees all reports
            reports = await self.repository.get_all(status=status, limit=limit)
        else:
            # Entity users see only their reports
            reports = await self.repository.get_by_entity_codes(
                entity_codes=user.entity_access,
                status=status,
                limit=limit
            )

        # Business Rule: Sort by priority (UKNF) or date (Entity)
        if user.is_uknf_user():
            # UKNF: Sort by risk score (high risk first), then by date
            reports.sort(
                key=lambda r: (
                    -(r.risk_score or 0),  # High risk first
                    -r.submitted_at.timestamp()  # Recent first
                )
            )
        else:
            # Entity: Sort by submission date (recent first)
            reports.sort(key=lambda r: -r.submitted_at.timestamp())

        return reports
