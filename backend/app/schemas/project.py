from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=50)
    project_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    construction_unit: Optional[str] = None
    location: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_duration: Optional[int] = None
    actual_start_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNING


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    construction_unit: Optional[str] = None
    location: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_duration: Optional[int] = None
    actual_start_date: Optional[date] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: UUID
    project_code: str
    project_name: str
    description: Optional[str]
    construction_unit: Optional[str]
    location: Optional[str]
    contract_start_date: Optional[date]
    contract_end_date: Optional[date]
    contract_duration: Optional[int]
    actual_start_date: Optional[date]
    status: ProjectStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int
