"""
Report Repository - Data persistence for reports
"""
from typing import List, Optional
from src.Entities import Report, ReportStatus

class ReportRepository:
    """
    In-memory Report Repository (Demo)
    In production: Replace with SQLAlchemy/PostgreSQL
    """

    def __init__(self):
        self._reports: Dict[str, Report] = {}

    async def save(self, report: Report) -> Report:
        """Save or update report"""
        self._reports[report.id] = report
        return report

    async def get_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        return self._reports.get(report_id)

    async def get_by_entity_codes(
        self, 
        entity_codes: List[str],
        status: Optional[ReportStatus] = None,
        limit: Optional[int] = None
    ) -> List[Report]:
        """Get reports for specific entities"""
        reports = [
            r for r in self._reports.values() 
            if r.entity_code in entity_codes
        ]

        if status:
            reports = [r for r in reports if r.status == status]

        if limit:
            reports = reports[:limit]

        return reports

    async def get_all(
        self,
        status: Optional[ReportStatus] = None,
        limit: Optional[int] = None
    ) -> List[Report]:
        """Get all reports"""
        reports = list(self._reports.values())

        if status:
            reports = [r for r in reports if r.status == status]

        if limit:
            reports = reports[:limit]

        return reports
