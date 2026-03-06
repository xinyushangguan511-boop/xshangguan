from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


class EngineeringDataCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    actual_duration: Optional[int] = None
    end_period_progress: Optional[str] = None
    contract_value: Optional[Decimal] = None
    monthly_output: Optional[Decimal] = None
    planned_output: Optional[Decimal] = None
    monthly_approval: Optional[Decimal] = None
    staff_count: Optional[int] = None
    next_month_plan: Optional[Decimal] = None
    remarks: Optional[str] = None


class EngineeringDataUpdate(BaseModel):
    actual_duration: Optional[int] = None
    end_period_progress: Optional[str] = None
    contract_value: Optional[Decimal] = None
    monthly_output: Optional[Decimal] = None
    planned_output: Optional[Decimal] = None
    monthly_approval: Optional[Decimal] = None
    staff_count: Optional[int] = None
    next_month_plan: Optional[Decimal] = None
    remarks: Optional[str] = None


class EngineeringDataResponse(BaseModel):
    id: UUID
    project_id: UUID
    year: int
    month: int
    actual_duration: Optional[int]
    end_period_progress: Optional[str]
    contract_value: Optional[Decimal]
    monthly_output: Optional[Decimal]
    planned_output: Optional[Decimal]
    monthly_approval: Optional[Decimal]
    staff_count: Optional[int]
    next_month_plan: Optional[Decimal]
    remarks: Optional[str]
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
