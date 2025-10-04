"""
User Domain Entity
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .enums import UserRole

class User(BaseModel):
    """
    User domain entity - represents authenticated user

    Business Rules:
    - Must have at least one role
    - Entity access determines report visibility
    - UKNF users have "*" entity access (all entities)
    """
    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email from OIDC")
    name: str = Field(..., description="Full name from OIDC")
    roles: List[UserRole] = Field(..., description="User roles")
    entity_access: List[str] = Field(..., description="Entity codes user can access")
    entity_names: List[str] = Field(default_factory=list, description="Human-readable entity names")

    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role"""
        return role in self.roles

    def can_access_entity(self, entity_code: str) -> bool:
        """Check if user can access specific entity"""
        return "*" in self.entity_access or entity_code in self.entity_access

    def is_uknf_user(self) -> bool:
        """Check if user is UKNF staff"""
        return UserRole.UKNF_SUPERVISOR in self.roles or UserRole.UKNF_ADMIN in self.roles
