from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Department
from app.models.project import Project
from app.models.finance import FinanceData
from app.schemas.finance import FinanceDataCreate, FinanceDataUpdate, FinanceDataResponse
from app.utils.dependencies import get_current_active_user, require_department

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/{project_id}/data", response_model=list[FinanceDataResponse])
async def list_finance_data(
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
        select(FinanceData)
        .where(FinanceData.project_id == project_id)
        .order_by(FinanceData.year.desc(), FinanceData.month.desc())
    )
    return list(result.scalars().all())


@router.post("/{project_id}/data", response_model=FinanceDataResponse)
async def create_finance_data(
    project_id: UUID,
    data: FinanceDataCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.FINANCE))],
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for duplicate year/month
    existing_result = await db.execute(
        select(FinanceData).where(
            FinanceData.project_id == project_id,
            FinanceData.year == data.year,
            FinanceData.month == data.month,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data for {data.year}-{data.month} already exists",
        )

    finance_data = FinanceData(
        project_id=project_id,
        created_by=current_user.id,
        **data.model_dump()
    )
    db.add(finance_data)
    await db.commit()
    await db.refresh(finance_data)
    return finance_data


@router.put("/{project_id}/data/{data_id}", response_model=FinanceDataResponse)
async def update_finance_data(
    project_id: UUID,
    data_id: UUID,
    data: FinanceDataUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.FINANCE))],
):
    result = await db.execute(
        select(FinanceData).where(
            FinanceData.id == data_id,
            FinanceData.project_id == project_id,
        )
    )
    finance_data = result.scalar_one_or_none()

    if not finance_data:
        raise HTTPException(status_code=404, detail="Finance data not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(finance_data, field, value)

    await db.commit()
    await db.refresh(finance_data)
    return finance_data


@router.delete("/{project_id}/data/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finance_data(
    project_id: UUID,
    data_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.FINANCE))],
):
    result = await db.execute(
        select(FinanceData).where(
            FinanceData.id == data_id,
            FinanceData.project_id == project_id,
        )
    )
    finance_data = result.scalar_one_or_none()

    if not finance_data:
        raise HTTPException(status_code=404, detail="Finance data not found")

    await db.delete(finance_data)
    await db.commit()
