from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


class MarketDataCreate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    building_area: Optional[Decimal] = None
    structure: Optional[str] = None
    floors: Optional[int] = None
    contract_value: Optional[Decimal] = None
    prepayment_ratio: Optional[Decimal] = None
    advance_amount: Optional[Decimal] = None
    progress_payment_ratio: Optional[Decimal] = None
    contract_type: Optional[str] = None
    remarks: Optional[str] = None


class MarketDataUpdate(BaseModel):
    building_area: Optional[Decimal] = None
    structure: Optional[str] = None
    floors: Optional[int] = None
    contract_value: Optional[Decimal] = None
    prepayment_ratio: Optional[Decimal] = None
    advance_amount: Optional[Decimal] = None
    progress_payment_ratio: Optional[Decimal] = None
    contract_type: Optional[str] = None
    remarks: Optional[str] = None


class MarketDataResponse(BaseModel):
    id: UUID
    project_id: UUID
    year: int
    month: int
    building_area: Optional[Decimal]
    structure: Optional[str]
    floors: Optional[int]
    contract_value: Optional[Decimal]
    prepayment_ratio: Optional[Decimal]
    advance_amount: Optional[Decimal]
    progress_payment_ratio: Optional[Decimal]
    contract_type: Optional[str]
    remarks: Optional[str]
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
