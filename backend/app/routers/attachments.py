import os
import uuid
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentResponse
from app.utils.dependencies import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


@router.get("/{project_id}", response_model=list[AttachmentResponse])
async def list_attachments(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Attachment)
        .where(Attachment.project_id == project_id)
        .order_by(Attachment.uploaded_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{project_id}/upload", response_model=AttachmentResponse)
async def upload_attachment(
    project_id: UUID,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[Optional[str], Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    # Create upload directory if not exists
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id))
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create attachment record
    attachment = Attachment(
        project_id=project_id,
        department=current_user.department,
        file_type=file_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return attachment


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        attachment.file_path,
        filename=attachment.file_name,
        media_type="application/octet-stream",
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Only uploader or admin can delete
    if attachment.uploaded_by != current_user.id and current_user.department.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete file from disk
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    await db.delete(attachment)
    await db.commit()
