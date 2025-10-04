"""
RiskAnalysis Value Object
"""
from pydantic import BaseModel, Field
from typing import List
from .enums import RiskLevel

class RiskAnalysis(BaseModel):
    """
    Risk analysis result from AI Categorizer Agent

    Business Rules:
    - Risk score 0-10 scale
    - Urgency affects UKNF queue prioritization
    - Reasoning chain provides audit trail
    """

    # Core analysis
    category: str = Field(..., description="Report category")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Risk score 0-10")
    risk_level: RiskLevel = Field(..., description="Derived risk level")
    urgency: str = Field(..., description="routine/urgent/critical")

    # Detailed findings
    anomalies: List[str] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)

    # AI reasoning (DeepSeek-reasoner output)
    reasoning_chain: str = Field(..., description="Complete AI reasoning process")
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Processing metadata
    processing_time: float = Field(..., description="Analysis time in seconds")
    agent_model: str = Field(default="deepseek-reasoner")

    def is_urgent(self) -> bool:
        """Business rule: Urgent if score > 7 or urgency="urgent/critical" """
        return self.risk_score > 7.0 or self.urgency in ["urgent", "critical"]

    def get_priority_score(self) -> int:
        """Calculate UKNF queue priority (higher = more urgent)"""
        base_score = int(self.risk_score * 10)
        urgency_bonus = {
            "routine": 0,
            "urgent": 20,  
            "critical": 50
        }.get(self.urgency, 0)
        anomaly_bonus = min(len(self.anomalies) * 5, 20)

        return base_score + urgency_bonus + anomaly_bonus
