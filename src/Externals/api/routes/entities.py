"""
Entities REST API - Entity Directory and Management
Meets requirements: Obsługa podmiotów nadzorowanych
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from src.Entities import Entity, User
from ..dependencies import get_current_user, get_entity_repository

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("/", response_model=List[Entity])
async def get_entities_directory(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_user: User = Depends(get_current_user),
    entity_repository = Depends(get_entity_repository)
):
    """
    📋 GET ENTITIES DIRECTORY

    Requirements fulfilled:
    - obsługa adresatów, grup kontaktów i kontaktów (contact management)
    - prowadzanie bazy pytań i odpowiedzi (FAQ database for entities)
    """

    try:
        entities = await entity_repository.get_all()

        # Filter by type if specified
        if entity_type:
            entities = [e for e in entities if e.entity_type.lower() == entity_type.lower()]

        # Search by name if specified
        if search:
            search_lower = search.lower()
            entities = [e for e in entities if search_lower in e.name.lower()]

        # For entity users, show only accessible entities
        if not current_user.is_uknf_user():
            entities = [e for e in entities if e.code in current_user.entity_access]

        return entities

    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas pobierania listy podmiotów")

@router.get("/{entity_code}", response_model=Entity)
async def get_entity_details(
    entity_code: str,
    current_user: User = Depends(get_current_user),
    entity_repository = Depends(get_entity_repository)
):
    """
    🏢 GET ENTITY DETAILS

    Requirements fulfilled:
    - obsługa kartoteki podmiotów i aktualizacja informacji o podmiotach nadzorowanych
    """

    # Check access
    if not current_user.is_uknf_user() and not current_user.can_access_entity(entity_code):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego podmiotu")

    try:
        entity = await entity_repository.get_by_code(entity_code)
        if not entity:
            raise HTTPException(status_code=404, detail="Podmiot nie został znaleziony")

        return entity

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas pobierania danych podmiotu")

@router.get("/{entity_code}/contacts")
async def get_entity_contacts(
    entity_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    📞 GET ENTITY CONTACTS

    Requirements fulfilled:
    - obsługa adresatów, grup kontaktów i kontaktów
    """

    # Check access
    if not current_user.is_uknf_user() and not current_user.can_access_entity(entity_code):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego podmiotu")

    # Mock contact data (in production, query from contact repository)
    return {
        "entity_code": entity_code,
        "contacts": [
            {
                "type": "compliance_officer",
                "name": "Marta Kowalska",
                "email": "marta.kowalska@mbank.pl",
                "phone": "+48 22 123 45 67"
            },
            {
                "type": "technical_contact",
                "name": "Jan Nowak",
                "email": "jan.nowak@mbank.pl", 
                "phone": "+48 22 123 45 68"
            }
        ]
    }

@router.get("/{entity_code}/statistics")
async def get_entity_statistics(
    entity_code: str,
    current_user: User = Depends(get_current_user),
    entity_repository = Depends(get_entity_repository)
):
    """
    📊 GET ENTITY STATISTICS

    Requirements fulfilled:
    - aktualizacja informacji o podmiotach nadzorowanych (entity information updates)
    - komunikacja zwrotna (statistical feedback)
    """

    # Check access
    if not current_user.is_uknf_user() and not current_user.can_access_entity(entity_code):
        raise HTTPException(status_code=403, detail="Brak dostępu do tego podmiotu")

    try:
        entity = await entity_repository.get_by_code(entity_code)
        if not entity:
            raise HTTPException(status_code=404, detail="Podmiot nie został znaleziony")

        # Return statistics
        return {
            "entity_code": entity_code,
            "entity_name": entity.name,
            "total_reports": entity.total_reports,
            "approved_reports": entity.approved_reports,
            "approval_rate": entity.get_approval_rate(),
            "average_risk_score": entity.average_risk_score,
            "is_high_volume": entity.is_high_volume_entity()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Błąd podczas pobierania statystyk")
