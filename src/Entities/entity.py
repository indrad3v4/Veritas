"""
Entity Domain Entity - Financial Institution
"""
from pydantic import BaseModel, Field
from typing import Optional

class Entity(BaseModel):
    """
    Financial Entity (Bank, Insurance Company, etc.)

    Business Rules:
    - Each entity has unique code (e.g., MBANK001)
    - Type determines regulatory requirements
    - LEI required for international entities
    """

    code: str = Field(..., description="Unique entity code")
    name: str = Field(..., description="Official entity name")
    short_name: str = Field(..., description="Short display name")

    # Legal identifiers
    nip: str = Field(..., description="Polish tax ID (NIP)")
    krs: Optional[str] = Field(None, description="Court registry number")
    lei: Optional[str] = Field(None, description="Legal Entity Identifier")

    # Entity classification
    entity_type: str = Field(..., description="bank/insurance/investment/other")

    # Statistics (for dashboards)
    total_reports: int = Field(default=0)
    approved_reports: int = Field(default=0)
    average_risk_score: Optional[float] = Field(None)

    class Config:
        use_enum_values = True

    def get_approval_rate(self) -> float:
        """Calculate approval rate percentage"""
        if self.total_reports == 0:
            return 0.0
        return (self.approved_reports / self.total_reports) * 100

    def is_high_volume_entity(self) -> bool:
        """Business rule: >50 reports = high volume"""
        return self.total_reports > 50
