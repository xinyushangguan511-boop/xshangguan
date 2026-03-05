from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.statistics import MarketSummary, EngineeringSummary, FinanceSummary, ProjectReport
from app.services.statistics_service import StatisticsService
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/market/summary", response_model=MarketSummary)
async def get_market_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[UUID] = None,
):
    service = StatisticsService(db)
    return await service.get_market_summary(project_id)


@router.get("/engineering/summary", response_model=EngineeringSummary)
async def get_engineering_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[UUID] = None,
):
    service = StatisticsService(db)
    return await service.get_engineering_summary(project_id)


@router.get("/finance/summary", response_model=FinanceSummary)
async def get_finance_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    project_id: Optional[UUID] = None,
):
    service = StatisticsService(db)
    return await service.get_finance_summary(project_id)


@router.get("/project/{project_id}/report", response_model=ProjectReport)
async def get_project_report(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = StatisticsService(db)
    report = await service.get_project_report(project_id)

    if not report:
        raise HTTPException(status_code=404, detail="Project not found")

    return report
