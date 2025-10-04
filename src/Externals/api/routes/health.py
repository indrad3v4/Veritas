"""
Health Check API - System monitoring
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import logging

from src.Gateways.agents import AgentOrchestrator
from ..dependencies import get_agent_orchestrator

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """
    ❤️ BASIC HEALTH CHECK
    """
    return {
        "status": "healthy",
        "service": "Veritas Backend API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development"
    }

@router.get("/agents")
async def agents_health_check(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    🤖 AI AGENTS HEALTH CHECK

    Verifies all AI agents are operational
    """
    try:
        agent_health = await orchestrator.health_check()

        return {
            "status": agent_health["status"],
            "agents": agent_health.get("agents", {}),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/detailed")
async def detailed_health_check(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    🔍 DETAILED SYSTEM HEALTH
    """

    health_data = {
        "service": "Veritas Backend API",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check AI agents
    try:
        agent_health = await orchestrator.health_check()
        health_data["components"]["ai_agents"] = {
            "status": agent_health["status"],
            "details": agent_health.get("agents", {})
        }
    except Exception as e:
        health_data["components"]["ai_agents"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"

    # Check database (mock)
    health_data["components"]["database"] = {
        "status": "healthy",
        "type": "SQLite",
        "connection": "ok"
    }

    # Check external services (mock)
    health_data["components"]["oidc"] = {
        "status": "healthy",
        "provider": "Keycloak",
        "connection": "ok"
    }

    return health_data
