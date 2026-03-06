import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = (
        UniqueConstraint("project_id", "year", "month", name="uix_market_project_year_month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    building_area: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    structure: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_value: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    prepayment_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    advance_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    progress_payment_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="market_data")
    creator = relationship("User", foreign_keys=[created_by])
