"""
Repository Gateways
"""
from .repository.report_repository import ReportRepository
from .repository.user_repository import UserRepository
from .repository.entity_repository import EntityRepository

__all__ = ["ReportRepository", "UserRepository", "EntityRepository"]
