from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class PeriodSummary(BaseModel):
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    total: Decimal


class MarketSummary(BaseModel):
    contract_value_monthly: list[PeriodSummary]
    contract_value_quarterly: list[PeriodSummary]
    contract_value_yearly: list[PeriodSummary]
    total_contract_value: Decimal


class EngineeringSummary(BaseModel):
    contract_value_monthly: list[PeriodSummary]
    contract_value_quarterly: list[PeriodSummary]
    contract_value_yearly: list[PeriodSummary]
    monthly_output_cumulative: list[PeriodSummary]
    monthly_approval_cumulative: list[PeriodSummary]
    total_output: Decimal
    total_approval: Decimal
    duration_ratio: Optional[Decimal] = None
    output_rate: Optional[Decimal] = None
    approval_rate: Optional[Decimal] = None
    per_capita_output: Optional[Decimal] = None


class FinanceSummary(BaseModel):
    revenue_quarterly: list[PeriodSummary]
    revenue_yearly: list[PeriodSummary]
    cost_quarterly: list[PeriodSummary]
    cost_yearly: list[PeriodSummary]
    payment_quarterly: list[PeriodSummary]
    payment_yearly: list[PeriodSummary]
    total_revenue: Decimal
    total_cost: Decimal
    total_payment: Decimal
    gross_margin: Optional[Decimal] = None


class ProjectReport(BaseModel):
    project_code: str
    project_name: str
    market_summary: Optional[MarketSummary] = None
    engineering_summary: Optional[EngineeringSummary] = None
    finance_summary: Optional[FinanceSummary] = None
