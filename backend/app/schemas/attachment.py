from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from app.models.user import Department


class AttachmentResponse(BaseModel):
    id: UUID
    project_id: UUID
    department: Department
    file_type: Optional[str]
    file_name: str
    file_path: str
    file_size: int
    uploaded_by: UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}
