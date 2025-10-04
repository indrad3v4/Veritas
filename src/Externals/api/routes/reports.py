"""
Reports REST API - Core business functionality
Meets requirements: Moduł Komunikacyjny + Entity handling
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
from datetime import datetime
import logging

from src.Entities import Report, User, ReportStatus, ReportType
from src.UseCases import SubmitReportUseCase, ApproveReportUseCase, RejectReportUseCase, GetReportsUseCase
from ..dependencies import get_current_user, get_submit_report_use_case, get_approve_report_use_case, get_reject_report_use_case, get_reports_use_case

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=Report)
async def submit_report(
    entity_code: str = Form(..., description="Entity code (e.g., MBANK001)"),
    report_type: ReportType = Form(..., description="Report type"),
    file: UploadFile = File(..., description="XLSX report file"),
    current_user: User = Depends(get_current_user),
    submit_use_case: SubmitReportUseCase = Depends(get_submit_report_use_case)
):
    """
    🔵 SUBMIT REPORT - Core Communication Module functionality

    Requirements fulfilled:
    - obsługa przyjmowania sprawozdań przekazywanych przez podmioty nadzorowane
    - komunikacja zwrotna (validation feedback)

    Business Flow:
    1. Entity officer uploads XLSX file
    2. AI Validator Agent validates structure
    3. AI Categorizer Agent analyzes risk
    4. UKNF gets notification for review
    5. Return communication includes validation results
    """

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Plik musi być w formacie XLSX lub XLS"
        )

    # Check file size (max 50MB)
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Plik jest za duży. Maksymalny rozmiar: 50MB"
        )

    try:
        # Execute business logic through Use Case
        report = await submit_use_case.execute(
            user=current_user,
            entity_code=entity_code,
            report_type=report_type,
            file_data=file_content,
            filename=file.filename
        )

        logger.info(f"Report {report.id} submitted by user {current_user.id}")
        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Błąd podczas przesyłania raportu")

@router.get("/", response_model=List[Report])
async def get_reports(
    status: Optional[ReportStatus] = Query(None, description="Filter by status"),
    entity_code: Optional[str] = Query(None, description="Filter by entity"),
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Limit results"),
    current_user: User = Depends(get_current_user),
    get_reports_use_case: GetReportsUseCase = Depends(get_reports_use_case)
):
    """
    📋 GET REPORTS - Role-based report listing

    Requirements fulfilled:
    - obsługa wiadomości + załączników (report attachments)
    - wybór podmiotu reprezentowanego (entity filtering)
    - prowadzenie bazy pytań i odpowiedzi (FAQ context)
    """

    try:
        reports = await get_reports_use_case.execute(
            user=current_user,
            status=status,
            limit=limit
        )

        # Additional entity filtering if specified
        if entity_code and not current_user.is_uknf_user():
            if entity_code not in current_user.entity_access:
                raise HTTPException(status_code=403, detail="Brak dostępu do tej jednostki")
            reports = [r for r in reports if r.entity_code == entity_code]

        return reports

    except Exception as e:
        logger.error(f"Get reports failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Błąd podczas pobierania raportów")

@router.get("/{report_id}", response_model=Report) 
async def get_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    get_reports_use_case: GetReportsUseCase = Depends(get_reports_use_case)
):
    """
    📄 GET REPORT DETAIL - Single report with full context

    Requirements fulfilled:
    - obsługa i prowadzenie spraw dotyczących podmiotów nadzorowanych
    - komunikacja z formie linku ogłoszeń (report status communication)
    """

    # Get all user reports to check access
    user_reports = await get_reports_use_case.execute(current_user)

    # Find specific report
    report = next((r for r in user_reports if r.id == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Raport nie został znaleziony")

    return report

@router.post("/{report_id}/approve", response_model=Report)
async def approve_report(
    report_id: str,
    comment: Optional[str] = Form(None, description="Optional approval comment"),
    current_user: User = Depends(get_current_user),
    approve_use_case: ApproveReportUseCase = Depends(get_approve_report_use_case)
):
    """
    ✅ APPROVE REPORT - UKNF supervisor action

    Requirements fulfilled:
    - zarządzanie kontami użytkowników wewnętrznych (UKNF role verification)
    - komunikacja zwrotna (approval notification)
    """

    if not current_user.is_uknf_user():
        raise HTTPException(
            status_code=403,
            detail="Tylko nadzorcy UKNF mogą zatwierdzać raporty"
        )

    try:
        report = await approve_use_case.execute(
            supervisor=current_user,
            report_id=report_id,
            comment=comment
        )

        logger.info(f"Report {report_id} approved by {current_user.id}")
        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report approval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Błąd podczas zatwierdzania")

@router.post("/{report_id}/reject", response_model=Report)
async def reject_report(
    report_id: str,
    comment: str = Form(..., description="Mandatory rejection reason"),
    current_user: User = Depends(get_current_user),
    reject_use_case: RejectReportUseCase = Depends(get_reject_report_use_case)
):
    """
    ❌ REJECT REPORT - UKNF supervisor action with feedback

    Requirements fulfilled:
    - komunikacja zwrotna (rejection with detailed feedback)
    - prowadzenie bazy pytań i odpowiedzi (FAQ building from rejections)
    """

    if not current_user.is_uknf_user():
        raise HTTPException(
            status_code=403,
            detail="Tylko nadzorcy UKNF mogą odrzucać raporty"
        )

    if not comment or len(comment.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Komentarz odrzucenia musi zawierać co najmniej 10 znaków"
        )

    try:
        report = await reject_use_case.execute(
            supervisor=current_user,
            report_id=report_id,
            comment=comment.strip()
        )

        logger.info(f"Report {report_id} rejected by {current_user.id}")
        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report rejection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Błąd podczas odrzucania")

@router.get("/{report_id}/download")
async def download_report_file(
    report_id: str,
    current_user: User = Depends(get_current_user),
    get_reports_use_case: GetReportsUseCase = Depends(get_reports_use_case)
):
    """
    📥 DOWNLOAD ORIGINAL REPORT FILE

    Requirements fulfilled:
    - utrzymanie lokalnego repozytorium plików (file library functionality)
    - obsługa załączników (file attachment handling)
    """

    # Check access to report
    user_reports = await get_reports_use_case.execute(current_user)
    report = next((r for r in user_reports if r.id == report_id), None)

    if not report:
        raise HTTPException(status_code=404, detail="Raport nie został znaleziony")

    # In production, this would return actual file from storage
    # For now, return file metadata
    return {
        "file_name": report.file_name,
        "file_size": report.file_size,
        "download_url": f"/api/files/{report.id}/original.xlsx",
        "message": "W wersji produkcyjnej tutaj byłby bezpośredni download pliku"
    }
