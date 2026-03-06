from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Department
from app.models.project import Project
from app.models.market import MarketData
from app.schemas.market import MarketDataCreate, MarketDataUpdate, MarketDataResponse
from app.utils.dependencies import get_current_active_user, require_department

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/{project_id}/data", response_model=list[MarketDataResponse])
async def list_market_data(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(MarketData)
        .where(MarketData.project_id == project_id)
        .order_by(MarketData.year.desc(), MarketData.month.desc())
    )
    return list(result.scalars().all())


@router.post("/{project_id}/data", response_model=MarketDataResponse)
async def create_market_data(
    project_id: UUID,
    data: MarketDataCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.MARKET))],
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for duplicate year/month
    existing_result = await db.execute(
        select(MarketData).where(
            MarketData.project_id == project_id,
            MarketData.year == data.year,
            MarketData.month == data.month,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data for {data.year}-{data.month} already exists",
        )

    market_data = MarketData(
        project_id=project_id,
        created_by=current_user.id,
        **data.model_dump()
    )
    db.add(market_data)
    await db.commit()
    await db.refresh(market_data)
    return market_data


@router.put("/{project_id}/data/{data_id}", response_model=MarketDataResponse)
async def update_market_data(
    project_id: UUID,
    data_id: UUID,
    data: MarketDataUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.MARKET))],
):
    result = await db.execute(
        select(MarketData).where(
            MarketData.id == data_id,
            MarketData.project_id == project_id,
        )
    )
    market_data = result.scalar_one_or_none()

    if not market_data:
        raise HTTPException(status_code=404, detail="Market data not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(market_data, field, value)

    await db.commit()
    await db.refresh(market_data)
    return market_data


@router.delete("/{project_id}/data/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_market_data(
    project_id: UUID,
    data_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.MARKET))],
):
    result = await db.execute(
        select(MarketData).where(
            MarketData.id == data_id,
            MarketData.project_id == project_id,
        )
    )
    market_data = result.scalar_one_or_none()

    if not market_data:
        raise HTTPException(status_code=404, detail="Market data not found")

    await db.delete(market_data)
    await db.commit()
