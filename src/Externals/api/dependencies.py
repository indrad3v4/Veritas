"""
FastAPI Dependencies - Dependency Injection Container
Clean Architecture dependency inversion
"""
import os
from typing import Annotated
from fastapi import Depends, HTTPException, Cookie, status
from jose import jwt, JWTError

from src.Entities import User
from src.UseCases import (
    SubmitReportUseCase, ApproveReportUseCase, RejectReportUseCase, 
    GetReportsUseCase, AuthenticateUserUseCase, NotifyUserUseCase
)
from src.Gateways.agents import AgentOrchestrator
from src.Gateways.auth import OIDCGateway, JWTValidator, SessionManager
from src.Gateways.repository import ReportRepository, UserRepository, EntityRepository
from src.Gateways.notifications import WebSocketGateway

# Global instances (in production, use proper DI container)
_agent_orchestrator = None
_oidc_gateway = None
_jwt_validator = None
_session_manager = None
_repositories = {}
_use_cases = {}

def get_agent_orchestrator() -> AgentOrchestrator:
    """Get AI Agent Orchestrator instance"""
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
    return _agent_orchestrator

def get_oidc_gateway() -> OIDCGateway:
    """Get OIDC Gateway instance"""
    global _oidc_gateway
    if _oidc_gateway is None:
        _oidc_gateway = OIDCGateway(
            issuer=os.getenv("OIDC_ISSUER"),
            client_id=os.getenv("OIDC_CLIENT_ID"),
            client_secret=os.getenv("OIDC_CLIENT_SECRET")
        )
    return _oidc_gateway

def get_jwt_validator() -> JWTValidator:
    """Get JWT Validator instance"""
    global _jwt_validator
    if _jwt_validator is None:
        _jwt_validator = JWTValidator(
            secret_key=os.getenv("SECRET_KEY"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256")
        )
    return _jwt_validator

def get_session_manager() -> SessionManager:
    """Get Session Manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(ttl_minutes=10)
    return _session_manager

# Repository dependencies
def get_report_repository() -> ReportRepository:
    global _repositories
    if "report" not in _repositories:
        _repositories["report"] = ReportRepository()
    return _repositories["report"]

def get_user_repository() -> UserRepository:
    global _repositories
    if "user" not in _repositories:
        _repositories["user"] = UserRepository()
    return _repositories["user"]

def get_entity_repository() -> EntityRepository:
    global _repositories
    if "entity" not in _repositories:
        _repositories["entity"] = EntityRepository()
    return _repositories["entity"]

def get_websocket_gateway() -> WebSocketGateway:
    return WebSocketGateway()

# Use Case dependencies (with proper dependency injection)
def get_submit_report_use_case(
    orchestrator: Annotated[AgentOrchestrator, Depends(get_agent_orchestrator)],
    report_repo: Annotated[ReportRepository, Depends(get_report_repository)],
    websocket: Annotated[WebSocketGateway, Depends(get_websocket_gateway)]
) -> SubmitReportUseCase:

    return SubmitReportUseCase(
        validator_agent=orchestrator.validator,
        categorizer_agent=orchestrator.categorizer,
        report_repository=report_repo,
        notification_gateway=websocket
    )

def get_approve_report_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repository)],
    websocket: Annotated[WebSocketGateway, Depends(get_websocket_gateway)]
) -> ApproveReportUseCase:

    return ApproveReportUseCase(
        report_repository=report_repo,
        notification_gateway=websocket
    )

def get_reject_report_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repository)],
    websocket: Annotated[WebSocketGateway, Depends(get_websocket_gateway)]
) -> RejectReportUseCase:

    return RejectReportUseCase(
        report_repository=report_repo,
        notification_gateway=websocket
    )

def get_reports_use_case(
    report_repo: Annotated[ReportRepository, Depends(get_report_repository)]
) -> GetReportsUseCase:

    return GetReportsUseCase(report_repository=report_repo)

def get_authenticate_user_use_case(
    oidc: Annotated[OIDCGateway, Depends(get_oidc_gateway)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthenticateUserUseCase:

    return AuthenticateUserUseCase(
        oidc_gateway=oidc,
        user_repository=user_repo
    )

# Authentication dependency
async def get_current_user(
    veritas_session: Annotated[str | None, Cookie()] = None,
    jwt_validator: Annotated[JWTValidator, Depends(get_jwt_validator)] = None,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)] = None
) -> User:
    """
    Extract current user from JWT token

    This dependency implements Clean Architecture:
    - Uses JWT validator (Gateway)
    - Queries user repository (Gateway)
    - Returns User entity (Domain)
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Brak autoryzacji",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not veritas_session:
        raise credentials_exception

    try:
        # Validate JWT token
        payload = jwt_validator.validate_token(veritas_session)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from repository
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user
