"""
Report Domain Entity - Core business entity
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .enums import ReportStatus, ReportType, RiskLevel

class Report(BaseModel):
    """
    Report domain entity - represents financial report submission

    Business Rules:
    - Entity can only submit reports for their own entity_code
    - UKNF can view/modify all reports
    - Status transitions: SUBMITTED → APPROVED/REJECTED/ESCALATED
    - Risk level derived from risk_score: <5=LOW, 5-7=MEDIUM, >7=HIGH
    """

    # Core identifiers
    id: str = Field(..., description="Unique report identifier")
    entity_code: str = Field(..., description="Entity identifier (e.g., MBANK001)")
    entity_name: str = Field(..., description="Human-readable entity name")

    # Report metadata
    report_type: ReportType = Field(..., description="Type of financial report")
    file_name: str = Field(..., description="Original XLSX filename")
    file_size: int = Field(..., description="File size in bytes")

    # Status and workflow
    status: ReportStatus = Field(..., description="Current report status")
    submitted_by: str = Field(..., description="User ID who submitted")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Validation results (from AI Validator Agent)
    validated_at: Optional[datetime] = None
    validation_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    # AI Analysis results (from AI Categorizer Agent)
    ai_category: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    risk_level: Optional[RiskLevel] = None
    anomalies: List[str] = Field(default_factory=list)
    reasoning_chain: Optional[str] = None  # DeepSeek thinking output
    analysis_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # UKNF decision
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None  # UKNF supervisor user_id
    decision_comment: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def is_high_risk(self) -> bool:
        """Business rule: High risk if score > 7.0"""
        return self.risk_score is not None and self.risk_score > 7.0

    def requires_escalation(self) -> bool:
        """Business rule: Escalate if high risk or multiple anomalies"""
        return self.is_high_risk() or len(self.anomalies) >= 3

    def can_be_approved_by(self, user_role: str) -> bool:
        """Business rule: Only UKNF supervisors can approve"""
        return user_role in ["uknf_supervisor", "uknf_admin"]

    def update_risk_analysis(
        self, 
        risk_score: float, 
        anomalies: List[str], 
        reasoning: str,
        confidence: float
    ):
        """Update AI analysis results with business rules"""
        self.risk_score = risk_score
        self.anomalies = anomalies
        self.reasoning_chain = reasoning
        self.analysis_confidence = confidence

        # Derive risk level from score (business rule)
        if risk_score < 5.0:
            self.risk_level = RiskLevel.LOW
        elif risk_score < 7.0:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.HIGH
