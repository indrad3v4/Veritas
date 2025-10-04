"""
Submit Report Use Case - Core business logic
"""
import uuid
from datetime import datetime
from typing import Protocol
from src.Entities import Report, User, ValidationResult, RiskAnalysis, ReportStatus, ReportType

# Gateway interfaces (dependency inversion)
class ValidatorAgentProtocol(Protocol):
    async def validate(self, file_data: bytes, filename: str) -> ValidationResult: ...

class CategorizerAgentProtocol(Protocol):
    async def analyze(self, file_data: bytes, report_type: str) -> RiskAnalysis: ...

class ReportRepositoryProtocol(Protocol):
    async def save(self, report: Report) -> Report: ...

class NotificationGatewayProtocol(Protocol):
    async def notify_report_submitted(self, report: Report) -> None: ...

class SubmitReportUseCase:
    """
    Business Logic: Submit Report with AI Validation & Risk Analysis

    Flow:
    1. Validate XLSX file structure (AI Validator)
    2. If invalid → Return draft with errors
    3. If valid → Analyze risk (AI Categorizer) 
    4. Save validated report
    5. Notify UKNF supervisors
    """

    def __init__(
        self,
        validator_agent: ValidatorAgentProtocol,
        categorizer_agent: CategorizerAgentProtocol,
        report_repository: ReportRepositoryProtocol,
        notification_gateway: NotificationGatewayProtocol
    ):
        self.validator = validator_agent
        self.categorizer = categorizer_agent
        self.repository = report_repository
        self.notifier = notification_gateway

    async def execute(
        self,
        user: User,
        entity_code: str,
        report_type: ReportType,
        file_data: bytes,
        filename: str
    ) -> Report:
        """
        Execute report submission use case

        Business Rules Applied:
        - User must have access to entity_code
        - File must pass AI validation
        - Risk analysis determines initial classification
        """

        # Business Rule: Check entity access
        if not user.can_access_entity(entity_code):
            raise ValueError(f"User {user.id} has no access to entity {entity_code}")

        # Step 1: AI Validation
        validation_result = await self.validator.validate(file_data, filename)

        # Create report entity
        report = Report(
            id=str(uuid.uuid4()),
            entity_code=entity_code,
            entity_name=self._get_entity_name(entity_code),
            report_type=report_type,
            file_name=filename,
            file_size=len(file_data),
            status=ReportStatus.VALIDATING,
            submitted_by=user.id,
            submitted_at=datetime.utcnow(),
            validated_at=datetime.utcnow(),
            validation_confidence=validation_result.confidence,
            validation_errors=[error for error in validation_result.errors],
            validation_warnings=validation_result.warnings
        )

        # Business Rule: Invalid reports become REJECTED
        if not validation_result.is_valid:
            report.status = ReportStatus.REJECTED
            await self.repository.save(report)
            return report

        # Step 2: AI Risk Analysis (only for valid reports)
        try:
            risk_analysis = await self.categorizer.analyze(file_data, report_type.value)

            # Update report with AI analysis
            report.update_risk_analysis(
                risk_score=risk_analysis.risk_score,
                anomalies=risk_analysis.anomalies,
                reasoning=risk_analysis.reasoning_chain,
                confidence=risk_analysis.confidence
            )
            report.ai_category = risk_analysis.category
            report.status = ReportStatus.SUBMITTED

        except Exception as e:
            # Fallback: Save without risk analysis
            report.status = ReportStatus.SUBMITTED
            report.validation_warnings.append(f"Risk analysis failed: {str(e)}")

        # Step 3: Save report
        saved_report = await self.repository.save(report)

        # Step 4: Notify UKNF (fire and forget)
        try:
            await self.notifier.notify_report_submitted(saved_report)
        except Exception:
            pass  # Don't fail submission if notification fails

        return saved_report

    def _get_entity_name(self, entity_code: str) -> str:
        """Get entity name from code (business lookup)"""
        # In real system, this would query entity repository
        entity_names = {
            "MBANK001": "mBank S.A.",
            "PKOBP001": "PKO Bank Polski S.A.",
            "PEKAO001": "Bank Pekao S.A.",
            "BZWBK001": "Santander Bank Polska S.A."
        }
        return entity_names.get(entity_code, f"Entity {entity_code}")
