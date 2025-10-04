"""
ValidationResult Value Object
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ValidationResult(BaseModel):
    """
    Validation result from AI Validator Agent

    Business Rules:
    - is_valid=False blocks report submission
    - Confidence < 0.8 triggers manual review
    - Errors must include column/row context for user fixes
    """

    is_valid: bool = Field(..., description="Overall validation result")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in validation")

    # Detailed feedback
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Validation errors with context"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    # Processing metadata
    processing_time: float = Field(..., description="Validation time in seconds")
    agent_model: str = Field(default="deepseek-chat")

    def has_critical_errors(self) -> bool:
        """Business rule: Critical errors prevent submission"""
        return not self.is_valid

    def needs_manual_review(self) -> bool:
        """Business rule: Low confidence needs human review"""
        return self.confidence < 0.8

    def get_user_friendly_summary(self) -> str:
        """Generate user-friendly validation summary"""
        if self.is_valid:
            return f"✅ Raport zwalidowany pomyślnie (pewność: {self.confidence:.1%})"
        else:
            error_count = len(self.errors)
            return f"❌ Znaleziono {error_count} błędów walidacji"
