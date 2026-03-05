from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Department
from app.models.project import Project, ProjectStatus
from app.models.engineering import EngineeringData
from app.schemas.engineering import EngineeringDataCreate, EngineeringDataUpdate, EngineeringDataResponse
from app.schemas.project import ProjectUpdate, ProjectResponse
from app.utils.dependencies import get_current_active_user, require_department

router = APIRouter(prefix="/api/engineering", tags=["engineering"])


@router.get("/{project_id}/data", response_model=list[EngineeringDataResponse])
async def list_engineering_data(
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
        select(EngineeringData)
        .where(EngineeringData.project_id == project_id)
        .order_by(EngineeringData.year.desc(), EngineeringData.month.desc())
    )
    return list(result.scalars().all())


@router.post("/{project_id}/data", response_model=EngineeringDataResponse)
async def create_engineering_data(
    project_id: UUID,
    data: EngineeringDataCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.ENGINEERING))],
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for duplicate year/month
    existing_result = await db.execute(
        select(EngineeringData).where(
            EngineeringData.project_id == project_id,
            EngineeringData.year == data.year,
            EngineeringData.month == data.month,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data for {data.year}-{data.month} already exists",
        )

    engineering_data = EngineeringData(project_id=project_id, **data.model_dump())
    db.add(engineering_data)
    await db.commit()
    await db.refresh(engineering_data)
    return engineering_data


@router.put("/{project_id}/data/{data_id}", response_model=EngineeringDataResponse)
async def update_engineering_data(
    project_id: UUID,
    data_id: UUID,
    data: EngineeringDataUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.ENGINEERING))],
):
    result = await db.execute(
        select(EngineeringData).where(
            EngineeringData.id == data_id,
            EngineeringData.project_id == project_id,
        )
    )
    engineering_data = result.scalar_one_or_none()

    if not engineering_data:
        raise HTTPException(status_code=404, detail="Engineering data not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(engineering_data, field, value)

    await db.commit()
    await db.refresh(engineering_data)
    return engineering_data


@router.delete("/{project_id}/data/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_engineering_data(
    project_id: UUID,
    data_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.ENGINEERING))],
):
    result = await db.execute(
        select(EngineeringData).where(
            EngineeringData.id == data_id,
            EngineeringData.project_id == project_id,
        )
    )
    engineering_data = result.scalar_one_or_none()

    if not engineering_data:
        raise HTTPException(status_code=404, detail="Engineering data not found")

    await db.delete(engineering_data)
    await db.commit()


@router.put("/{project_id}/status", response_model=ProjectResponse)
async def update_project_status(
    project_id: UUID,
    status_update: ProjectStatus,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_department(Department.ENGINEERING))],
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = status_update
    await db.commit()
    await db.refresh(project)
    return project
