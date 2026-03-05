from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


class FinanceDataCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    monthly_revenue: Optional[Decimal] = None
    monthly_cost: Optional[Decimal] = None
    monthly_payment_received: Optional[Decimal] = None
    target_margin: Optional[Decimal] = None
    remarks: Optional[str] = None


class FinanceDataUpdate(BaseModel):
    monthly_revenue: Optional[Decimal] = None
    monthly_cost: Optional[Decimal] = None
    monthly_payment_received: Optional[Decimal] = None
    target_margin: Optional[Decimal] = None
    remarks: Optional[str] = None


class FinanceDataResponse(BaseModel):
    id: UUID
    project_id: UUID
    year: int
    month: int
    monthly_revenue: Optional[Decimal]
    monthly_cost: Optional[Decimal]
    monthly_payment_received: Optional[Decimal]
    target_margin: Optional[Decimal]
    remarks: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
