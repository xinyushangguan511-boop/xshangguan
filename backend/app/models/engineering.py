import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EngineeringData(Base):
    __tablename__ = "engineering_data"
    __table_args__ = (
        UniqueConstraint("project_id", "year", "month", name="uix_engineering_project_year_month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_period_progress: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contract_value: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    monthly_output: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    planned_output: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    monthly_approval: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    staff_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_month_plan: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="engineering_data")
