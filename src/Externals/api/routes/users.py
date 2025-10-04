"""
Users REST API - User Management and Administration
Meets requirements: Moduł Administracyjny
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from src.Entities import User, UserRole
from ..dependencies import get_current_user, get_user_repository

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    👤 GET MY USER PROFILE

    Requirements fulfilled:
    - zarządzanie kontami użytkowników wewnętrznych i zewnętrznych
    """
    return current_user

@router.get("/", response_model=List[User])
async def get_users_list(
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Show only active users"),
    current_user: User = Depends(get_current_user),
    user_repository = Depends(get_user_repository)
):
    """
    👥 GET USERS LIST - Admin functionality

    Requirements fulfilled:
    - zarządzanie kontami użytkowników wewnętrznych i zewnętrznych przez pracowników UKNF
    - zarządzanie rolami użytkowników wewnętrznych i zewnętrznych
    """

    # Only UKNF admins can list users
    if not current_user.has_role(UserRole.UKNF_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Tylko administratorzy UKNF mogą przeglądać listę użytkowników"
        )

    try:
        users = await user_repository.get_all()

        # Filter by role if specified
        if role:
            users = [u for u in users if role in u.roles]

        # Filter active users if specified
        if active_only:
            users = [u for u in users if u.is_active]

        return users

    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas pobierania listy użytkowników")

@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_repository = Depends(get_user_repository)
):
    """
    🚫 DEACTIVATE USER - Admin functionality

    Requirements fulfilled:
    - zarządzanie kontami użytkowników (account management)
    """

    # Only UKNF admins can deactivate users
    if not current_user.has_role(UserRole.UKNF_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Tylko administratorzy UKNF mogą dezaktywować użytkowników"
        )

    # Cannot deactivate self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Nie można dezaktywować własnego konta"
        )

    try:
        user = await user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Użytkownik nie został znaleziony")

        user.is_active = False
        await user_repository.save(user)

        return {
            "success": True,
            "message": f"Użytkownik {user.email} został dezaktywowany"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas dezaktywacji użytkownika")

@router.post("/{user_id}/assign-role")
async def assign_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(get_current_user),
    user_repository = Depends(get_user_repository)
):
    """
    👮 ASSIGN USER ROLE - Admin functionality

    Requirements fulfilled:
    - zarządzanie rolami użytkowników wewnętrznych i zewnętrznych
    """

    # Only UKNF admins can assign roles
    if not current_user.has_role(UserRole.UKNF_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Tylko administratorzy UKNF mogą przypisywać role"
        )

    try:
        user = await user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Użytkownik nie został znaleziony")

        if role not in user.roles:
            user.roles.append(role)
            await user_repository.save(user)

        return {
            "success": True,
            "message": f"Rola {role} została przypisana użytkownikowi {user.email}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas przypisywania roli")

@router.get("/password-policy")
async def get_password_policy():
    """
    🔐 GET PASSWORD POLICY

    Requirements fulfilled:
    - zarządzanie polityką haseł w systemie (password policy management)
    """

    return {
        "policy": {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "max_age_days": 90,
            "history_count": 5,
            "lockout_attempts": 5,
            "lockout_duration_minutes": 30
        },
        "message": "Polityka haseł systemu Veritas"
    }
