import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Text, Integer, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FinanceData(Base):
    __tablename__ = "finance_data"
    __table_args__ = (
        UniqueConstraint("project_id", "year", "month", name="uix_finance_project_year_month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_revenue: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    monthly_cost: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    monthly_payment_received: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    target_margin: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="finance_data")
