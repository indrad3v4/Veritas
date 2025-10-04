"""
Domain Enums - Business Value Objects
"""
from enum import Enum

class ReportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

class UserRole(str, Enum):
    ENTITY_OFFICER = "entity_officer"
    UKNF_SUPERVISOR = "uknf_supervisor"
    UKNF_ADMIN = "uknf_admin"

class RiskLevel(str, Enum):
    LOW = "low"         # < 5.0
    MEDIUM = "medium"   # 5.0-7.0
    HIGH = "high"       # > 7.0

class ReportType(str, Enum):
    LIQUIDITY = "liquidity"
    AML = "aml"
    CAPITAL = "capital"
    GOVERNANCE = "governance"

class NotificationType(str, Enum):
    REPORT_SUBMITTED = "report_submitted"
    REPORT_APPROVED = "report_approved" 
    REPORT_REJECTED = "report_rejected"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ALERT = "system_alert"
