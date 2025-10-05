"""
Authentication REST API - OIDC Integration
Moduł Uwierzytelnienia i Autoryzacji
File: src/Externals/api/routes/auth.py
"""
import os
import secrets
import logging
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, Query, status
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any

from src.Entities import User
from src.UseCases import AuthenticateUserUseCase
from ..dependencies import (get_authenticate_user_use_case, get_oidc_gateway,
                            get_current_user, get_session_manager)

# FIXED: Use /api/auth prefix to match what's registered
router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.get("/login")
async def initiate_oidc_login(
    request: Request,
    oidc_gateway=Depends(get_oidc_gateway),
    session_manager=Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    🔐 INITIATE OIDC LOGIN

    Requirements fulfilled:
    - rejestrację użytkowników zewnętrznych poprzez formularz online
    - obsługę wniosków o dostęp (access request handling)
    """
    try:
        # Build redirect URI for callback - FIXED TO MATCH ACTUAL PREFIX
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/api/auth/callback"  # Match router prefix

        # Fetch OIDC metadata
        metadata = await oidc_gateway.get_metadata()
        # Generate PKCE challenge & state
        pkce = oidc_gateway.generate_pkce_challenge()
        state = secrets.token_urlsafe(32)

        # Store session data
        session_manager.create_session(state, pkce["code_verifier"],
                                       redirect_uri)

        # Build authorization URL
        auth_endpoint = metadata["authorization_endpoint"]
        params = {
            "client_id": oidc_gateway.client_id,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": pkce["code_challenge_method"]
        }
        authorization_url = f"{auth_endpoint}?{urlencode(params)}"
        return {"authorization_url": authorization_url}

    except Exception as e:
        logger.error(f"OIDC login initiation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Login initialization failed")


@router.get("/callback")
async def handle_oidc_callback(
    response: Response,
    code: str = Query(..., description="Authorization code from OIDC provider"),
    state: str = Query(..., description="State token for CSRF protection"),
    authenticate_use_case: AuthenticateUserUseCase = Depends(
        get_authenticate_user_use_case),
    oidc_gateway=Depends(get_oidc_gateway),
    session_manager=Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    🎯 HANDLE OIDC CALLBACK

    Requirements fulfilled:
    - wybór podmiotu reprezentowanego w ramach sesji (session entity selection)
    - uwierzytelnieniu użytkownika zewnętrznego (external user authentication)
    """
    try:

        session_data = session_manager.get_session(state)
        if not session_data:
            raise ValueError("Invalid or expired state token")

        code_verifier = session_data["code_verifier"]
        redirect_uri = session_data["redirect_uri"]
        session_manager.delete_session(state)

        tokens = await oidc_gateway.exchange_code_for_tokens(
            code=code, code_verifier=code_verifier, redirect_uri=redirect_uri)
        user: User = await authenticate_use_case.execute(tokens["id_token"])

        response.set_cookie(key="veritas_session",
                            value=tokens["access_token"],
                            httponly=True,
                            secure=(os.getenv("ENVIRONMENT") == "production"),
                            samesite="lax",
                            max_age=86400)
        logger.info(f"User {user.email} authenticated successfully")
        return {
            "success": True,
            "user": user,
            "message": "Uwierzytelnienie zakończone pomyślnie"
        }

    except Exception as e:
        logger.error(f"OIDC callback failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Błąd uwierzytelnienia: {str(e)}")


@router.post("/logout")
async def logout_user(response: Response) -> Dict[str, Any]:
    """
    🚪 LOGOUT USER

    Requirements fulfilled:
    - zarządzanie sesjami użytkowników (session management)
    """
    response.delete_cookie("veritas_session")
    return {"success": True, "message": "Użytkownik został wylogowany"}


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(
    get_current_user)) -> User:
    """
    👤 GET CURRENT USER PROFILE
    Requirements fulfilled:
    - zarządzanie kontami użytkowników zewnętrznych
    - wyświetlanie informacji o użytkowniku
    """
    return current_user


@router.post("/select-entity")
async def select_representative_entity(
        entity_code: str = Form(...),
        current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    🏢 SELECT ENTITY
    Requirements fulfilled:
    - wybór podmiotu reprezentowanego w ramach sesji
    """
    if not current_user.can_access_entity(entity_code):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Brak dostępu do podmiotu")
    entity_name = next(
        (n
         for c, n in zip(current_user.entity_access, current_user.entity_names)
         if c == entity_code), entity_code)
    return {
        "success": True,
        "selected_entity": {
            "code": entity_code,
            "name": entity_name
        }
    }
