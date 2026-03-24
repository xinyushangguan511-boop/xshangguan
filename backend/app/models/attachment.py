import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import Department


class AttachmentModule(str, PyEnum):
    """附件所属板块"""
    PROJECT = "project"  # 项目级附件
    MARKET = "market"    # 市场数据板块
    ENGINEERING = "engineering"  # 工程数据板块
    FINANCE = "finance"  # 财务数据板块


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    module: Mapped[AttachmentModule] = mapped_column(
        Enum(AttachmentModule), default=AttachmentModule.PROJECT, nullable=False
    )
    department: Mapped[Department] = mapped_column(Enum(Department), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")
