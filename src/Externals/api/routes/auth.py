"""
Authentication REST API - OIDC Integration
Meets requirements: Moduł Uwierzytelnienia i Autoryzacji
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import RedirectResponse
from typing import Dict, Any
import logging

from src.Entities import User
from src.UseCases import AuthenticateUserUseCase
from ..dependencies import get_authenticate_user_use_case, get_oidc_gateway

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

@router.get("/login")
async def initiate_oidc_login(
    request: Request,
    oidc_gateway = Depends(get_oidc_gateway)
):
    """
    🔐 INITIATE OIDC LOGIN

    Requirements fulfilled:
    - rejestrację użytkowników zewnętrznych poprzez formularz online
    - obsługę wniosków o dostęp (access request handling)
    """

    try:
        # Generate OIDC authorization URL
        authorization_url = await oidc_gateway.get_authorization_url(
            redirect_uri=str(request.base_url) + "api/auth/callback"
        )

        return {
            "authorization_url": authorization_url,
            "message": "Przekieruj użytkownika na podany URL do logowania OIDC"
        }

    except Exception as e:
        logger.error(f"OIDC login initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Błąd inicjalizacji logowania")

@router.post("/callback")
async def handle_oidc_callback(
    code: str = Form(...),
    state: str = Form(...),
    code_verifier: str = Form(...),
    response: Response,
    authenticate_use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case),
    oidc_gateway = Depends(get_oidc_gateway)
):
    """
    🎯 HANDLE OIDC CALLBACK

    Requirements fulfilled:
    - wybór podmiotu reprezentowanego w ramach sesji (session entity selection)
    - uwierzytelnieniu użytkownika zewnętrznego (external user authentication)
    """

    try:
        # Exchange authorization code for tokens
        tokens = await oidc_gateway.exchange_code_for_tokens(
            code=code,
            code_verifier=code_verifier,
            state=state
        )

        # Authenticate user through business logic
        user = await authenticate_use_case.execute(tokens["id_token"])

        # Set secure HTTP-only cookie
        response.set_cookie(
            key="veritas_session",
            value=tokens["access_token"],
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400  # 24 hours
        )

        logger.info(f"User {user.email} authenticated successfully")

        return {
            "success": True,
            "user": user,
            "message": "Uwierzytelnienie zakończone pomyślnie"
        }

    except Exception as e:
        logger.error(f"OIDC callback failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Błąd uwierzytelnienia: {str(e)}")

@router.post("/logout")
async def logout_user(response: Response):
    """
    🚪 LOGOUT USER

    Requirements fulfilled:
    - zarządzanie sesjami użytkowników (session management)
    """

    response.delete_cookie("veritas_session")

    return {
        "success": True,
        "message": "Użytkownik został wylogowany"
    }

@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    👤 GET CURRENT USER PROFILE

    Requirements fulfilled:
    - zarządzanie kontami użytkowników zewnętrznych (external user account management)
    - wyświetlanie informacji o użytkowniku (user profile display)
    """

    return current_user

@router.post("/select-entity")
async def select_representative_entity(
    entity_code: str = Form(..., description="Entity code to represent"),
    current_user: User = Depends(get_current_user)
):
    """
    🏢 SELECT REPRESENTATIVE ENTITY

    Requirements fulfilled:
    - wybór podmiotu reprezentowanego w ramach sesji przez uwierzytelnionego użytkownika zewnętrznego
    """

    if not current_user.can_access_entity(entity_code):
        raise HTTPException(
            status_code=403,
            detail="Użytkownik nie ma dostępu do tego podmiotu"
        )

    # In production, this would update session state
    # For now, return confirmation
    entity_name = next(
        (name for code, name in zip(current_user.entity_access, current_user.entity_names) 
         if code == entity_code), 
        f"Entity {entity_code}"
    )

    return {
        "success": True,
        "selected_entity": {
            "code": entity_code,
            "name": entity_name
        },
        "message": f"Wybrano podmiot: {entity_name}"
    }
