from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.project import Project
from app.models.market import MarketData
from app.models.engineering import EngineeringData
from app.models.finance import FinanceData
from app.schemas.statistics import (
    PeriodSummary,
    MarketSummary,
    EngineeringSummary,
    FinanceSummary,
    ProjectReport,
)


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_market_summary(self, project_id: UUID = None) -> MarketSummary:
        base_query = select(MarketData)
        if project_id:
            base_query = base_query.where(MarketData.project_id == project_id)

        # Monthly contract values
        monthly_query = (
            select(
                MarketData.year,
                MarketData.month,
                func.sum(MarketData.contract_value).label("total"),
            )
            .group_by(MarketData.year, MarketData.month)
            .order_by(MarketData.year, MarketData.month)
        )
        if project_id:
            monthly_query = monthly_query.where(MarketData.project_id == project_id)

        monthly_result = await self.db.execute(monthly_query)
        monthly_data = [
            PeriodSummary(year=row.year, month=row.month, total=row.total or Decimal(0))
            for row in monthly_result.all()
        ]

        # Quarterly
        quarterly_query = (
            select(
                MarketData.year,
                ((MarketData.month - 1) / 3 + 1).label("quarter"),
                func.sum(MarketData.contract_value).label("total"),
            )
            .group_by(MarketData.year, "quarter")
            .order_by(MarketData.year, "quarter")
        )
        if project_id:
            quarterly_query = quarterly_query.where(MarketData.project_id == project_id)

        quarterly_result = await self.db.execute(quarterly_query)
        quarterly_data = [
            PeriodSummary(year=row.year, quarter=int(row.quarter), total=row.total or Decimal(0))
            for row in quarterly_result.all()
        ]

        # Yearly
        yearly_query = (
            select(
                MarketData.year,
                func.sum(MarketData.contract_value).label("total"),
            )
            .group_by(MarketData.year)
            .order_by(MarketData.year)
        )
        if project_id:
            yearly_query = yearly_query.where(MarketData.project_id == project_id)

        yearly_result = await self.db.execute(yearly_query)
        yearly_data = [
            PeriodSummary(year=row.year, total=row.total or Decimal(0))
            for row in yearly_result.all()
        ]

        # Total
        total_query = select(func.sum(MarketData.contract_value))
        if project_id:
            total_query = total_query.where(MarketData.project_id == project_id)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or Decimal(0)

        return MarketSummary(
            contract_value_monthly=monthly_data,
            contract_value_quarterly=quarterly_data,
            contract_value_yearly=yearly_data,
            total_contract_value=total,
        )

    async def get_engineering_summary(self, project_id: UUID = None) -> EngineeringSummary:
        # Monthly output
        monthly_output_query = (
            select(
                EngineeringData.year,
                EngineeringData.month,
                func.sum(EngineeringData.monthly_output).label("total"),
            )
            .group_by(EngineeringData.year, EngineeringData.month)
            .order_by(EngineeringData.year, EngineeringData.month)
        )
        if project_id:
            monthly_output_query = monthly_output_query.where(EngineeringData.project_id == project_id)

        monthly_result = await self.db.execute(monthly_output_query)
        monthly_output_data = [
            PeriodSummary(year=row.year, month=row.month, total=row.total or Decimal(0))
            for row in monthly_result.all()
        ]

        # Monthly approval
        monthly_approval_query = (
            select(
                EngineeringData.year,
                EngineeringData.month,
                func.sum(EngineeringData.monthly_approval).label("total"),
            )
            .group_by(EngineeringData.year, EngineeringData.month)
            .order_by(EngineeringData.year, EngineeringData.month)
        )
        if project_id:
            monthly_approval_query = monthly_approval_query.where(EngineeringData.project_id == project_id)

        approval_result = await self.db.execute(monthly_approval_query)
        monthly_approval_data = [
            PeriodSummary(year=row.year, month=row.month, total=row.total or Decimal(0))
            for row in approval_result.all()
        ]

        # Contract value quarterly
        quarterly_query = (
            select(
                EngineeringData.year,
                ((EngineeringData.month - 1) / 3 + 1).label("quarter"),
                func.sum(EngineeringData.contract_value).label("total"),
            )
            .group_by(EngineeringData.year, "quarter")
            .order_by(EngineeringData.year, "quarter")
        )
        if project_id:
            quarterly_query = quarterly_query.where(EngineeringData.project_id == project_id)

        quarterly_result = await self.db.execute(quarterly_query)
        quarterly_data = [
            PeriodSummary(year=row.year, quarter=int(row.quarter), total=row.total or Decimal(0))
            for row in quarterly_result.all()
        ]

        # Yearly
        yearly_query = (
            select(
                EngineeringData.year,
                func.sum(EngineeringData.contract_value).label("total"),
            )
            .group_by(EngineeringData.year)
            .order_by(EngineeringData.year)
        )
        if project_id:
            yearly_query = yearly_query.where(EngineeringData.project_id == project_id)

        yearly_result = await self.db.execute(yearly_query)
        yearly_data = [
            PeriodSummary(year=row.year, total=row.total or Decimal(0))
            for row in yearly_result.all()
        ]

        # Monthly contract values
        monthly_cv_query = (
            select(
                EngineeringData.year,
                EngineeringData.month,
                func.sum(EngineeringData.contract_value).label("total"),
            )
            .group_by(EngineeringData.year, EngineeringData.month)
            .order_by(EngineeringData.year, EngineeringData.month)
        )
        if project_id:
            monthly_cv_query = monthly_cv_query.where(EngineeringData.project_id == project_id)

        monthly_cv_result = await self.db.execute(monthly_cv_query)
        monthly_cv_data = [
            PeriodSummary(year=row.year, month=row.month, total=row.total or Decimal(0))
            for row in monthly_cv_result.all()
        ]

        # Totals
        totals_query = select(
            func.sum(EngineeringData.monthly_output),
            func.sum(EngineeringData.monthly_approval),
        )
        if project_id:
            totals_query = totals_query.where(EngineeringData.project_id == project_id)

        totals_result = await self.db.execute(totals_query)
        totals = totals_result.one()
        total_output = totals[0] or Decimal(0)
        total_approval = totals[1] or Decimal(0)

        # Calculate ratios
        approval_rate = None
        if total_output > 0:
            approval_rate = (total_approval / total_output) * 100

        return EngineeringSummary(
            contract_value_monthly=monthly_cv_data,
            contract_value_quarterly=quarterly_data,
            contract_value_yearly=yearly_data,
            monthly_output_cumulative=monthly_output_data,
            monthly_approval_cumulative=monthly_approval_data,
            total_output=total_output,
            total_approval=total_approval,
            approval_rate=approval_rate,
        )

    async def get_finance_summary(self, project_id: UUID = None) -> FinanceSummary:
        # Revenue quarterly
        revenue_quarterly_query = (
            select(
                FinanceData.year,
                ((FinanceData.month - 1) / 3 + 1).label("quarter"),
                func.sum(FinanceData.monthly_revenue).label("total"),
            )
            .group_by(FinanceData.year, "quarter")
            .order_by(FinanceData.year, "quarter")
        )
        if project_id:
            revenue_quarterly_query = revenue_quarterly_query.where(FinanceData.project_id == project_id)

        revenue_q_result = await self.db.execute(revenue_quarterly_query)
        revenue_quarterly = [
            PeriodSummary(year=row.year, quarter=int(row.quarter), total=row.total or Decimal(0))
            for row in revenue_q_result.all()
        ]

        # Revenue yearly
        revenue_yearly_query = (
            select(
                FinanceData.year,
                func.sum(FinanceData.monthly_revenue).label("total"),
            )
            .group_by(FinanceData.year)
            .order_by(FinanceData.year)
        )
        if project_id:
            revenue_yearly_query = revenue_yearly_query.where(FinanceData.project_id == project_id)

        revenue_y_result = await self.db.execute(revenue_yearly_query)
        revenue_yearly = [
            PeriodSummary(year=row.year, total=row.total or Decimal(0))
            for row in revenue_y_result.all()
        ]

        # Cost quarterly
        cost_quarterly_query = (
            select(
                FinanceData.year,
                ((FinanceData.month - 1) / 3 + 1).label("quarter"),
                func.sum(FinanceData.monthly_cost).label("total"),
            )
            .group_by(FinanceData.year, "quarter")
            .order_by(FinanceData.year, "quarter")
        )
        if project_id:
            cost_quarterly_query = cost_quarterly_query.where(FinanceData.project_id == project_id)

        cost_q_result = await self.db.execute(cost_quarterly_query)
        cost_quarterly = [
            PeriodSummary(year=row.year, quarter=int(row.quarter), total=row.total or Decimal(0))
            for row in cost_q_result.all()
        ]

        # Cost yearly
        cost_yearly_query = (
            select(
                FinanceData.year,
                func.sum(FinanceData.monthly_cost).label("total"),
            )
            .group_by(FinanceData.year)
            .order_by(FinanceData.year)
        )
        if project_id:
            cost_yearly_query = cost_yearly_query.where(FinanceData.project_id == project_id)

        cost_y_result = await self.db.execute(cost_yearly_query)
        cost_yearly = [
            PeriodSummary(year=row.year, total=row.total or Decimal(0))
            for row in cost_y_result.all()
        ]

        # Payment quarterly
        payment_quarterly_query = (
            select(
                FinanceData.year,
                ((FinanceData.month - 1) / 3 + 1).label("quarter"),
                func.sum(FinanceData.monthly_payment_received).label("total"),
            )
            .group_by(FinanceData.year, "quarter")
            .order_by(FinanceData.year, "quarter")
        )
        if project_id:
            payment_quarterly_query = payment_quarterly_query.where(FinanceData.project_id == project_id)

        payment_q_result = await self.db.execute(payment_quarterly_query)
        payment_quarterly = [
            PeriodSummary(year=row.year, quarter=int(row.quarter), total=row.total or Decimal(0))
            for row in payment_q_result.all()
        ]

        # Payment yearly
        payment_yearly_query = (
            select(
                FinanceData.year,
                func.sum(FinanceData.monthly_payment_received).label("total"),
            )
            .group_by(FinanceData.year)
            .order_by(FinanceData.year)
        )
        if project_id:
            payment_yearly_query = payment_yearly_query.where(FinanceData.project_id == project_id)

        payment_y_result = await self.db.execute(payment_yearly_query)
        payment_yearly = [
            PeriodSummary(year=row.year, total=row.total or Decimal(0))
            for row in payment_y_result.all()
        ]

        # Totals
        totals_query = select(
            func.sum(FinanceData.monthly_revenue),
            func.sum(FinanceData.monthly_cost),
            func.sum(FinanceData.monthly_payment_received),
        )
        if project_id:
            totals_query = totals_query.where(FinanceData.project_id == project_id)

        totals_result = await self.db.execute(totals_query)
        totals = totals_result.one()
        total_revenue = totals[0] or Decimal(0)
        total_cost = totals[1] or Decimal(0)
        total_payment = totals[2] or Decimal(0)

        # Gross margin
        gross_margin = None
        if total_revenue > 0:
            gross_margin = ((total_revenue - total_cost) / total_revenue) * 100

        return FinanceSummary(
            revenue_quarterly=revenue_quarterly,
            revenue_yearly=revenue_yearly,
            cost_quarterly=cost_quarterly,
            cost_yearly=cost_yearly,
            payment_quarterly=payment_quarterly,
            payment_yearly=payment_yearly,
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_payment=total_payment,
            gross_margin=gross_margin,
        )

    async def get_project_report(self, project_id: UUID) -> ProjectReport:
        # Get project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            return None

        market_summary = await self.get_market_summary(project_id)
        engineering_summary = await self.get_engineering_summary(project_id)
        finance_summary = await self.get_finance_summary(project_id)

        return ProjectReport(
            project_code=project.project_code,
            project_name=project.project_name,
            market_summary=market_summary,
            engineering_summary=engineering_summary,
            finance_summary=finance_summary,
        )
