import os
import uuid
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.attachment import Attachment, AttachmentModule
from app.schemas.attachment import AttachmentResponse
from app.utils.dependencies import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/attachments", tags=["attachments"])


@router.get("/{project_id}", response_model=list[AttachmentResponse])
async def list_attachments(
    project_id: UUID,
    module: Annotated[Optional[str], Query(description="可选：按板块筛选 (project/market/engineering/finance)")] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    查询项目的附件列表
    :param project_id: 项目ID
    :param module: 可选的板块筛选（project/market/engineering/finance）
    """
    # Check project exists
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = select(Attachment).where(Attachment.project_id == project_id)
    
    # 查询参数传入的是字符串（如 market），
    # 必须先转AttachmentModule再交给ORM，避免与数据库enum比较时类型不一致。
    if module:
        try:
            attachment_module = AttachmentModule(module)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module. Allowed: {[m.value for m in AttachmentModule]}"
            )

        query = query.where(Attachment.module == attachment_module)
    
    query = query.order_by(Attachment.uploaded_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{project_id}/upload", response_model=AttachmentResponse)
async def upload_attachment(
    project_id: UUID,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[Optional[str], Form()] = None,
    module: Annotated[Optional[str], Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    通用附件上传端点（支持各板块）
    :param project_id: 项目ID
    :param file: 上传文件
    :param file_type: 文件类型标签（可选）
    :param module: 板块（project/market/engineering/finance，默认为project）
    """
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

    # 新增module字段后，通用上传接口默认归入project模块，
    # 同时允许前端按market/engineering/finance显式指定。
    attachment_module = AttachmentModule.PROJECT
    if module:
        try:
            attachment_module = AttachmentModule(module)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module. Allowed: {[m.value for m in AttachmentModule]}"
            )

    # Create attachment record
    attachment = Attachment(
        project_id=project_id,
        module=attachment_module,
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


@router.post("/{project_id}/market/upload", response_model=AttachmentResponse)
async def upload_market_attachment(
    project_id: UUID,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[Optional[str], Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    市场数据板块专用附件上传
    :param project_id: 项目ID
    :param file: 上传文件
    :param file_type: 文件类型标签（如：市场调研报告、竞争对手分析等）
    """
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
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id), "market")
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
        module=AttachmentModule.MARKET,
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


@router.post("/{project_id}/engineering/upload", response_model=AttachmentResponse)
async def upload_engineering_attachment(
    project_id: UUID,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[Optional[str], Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    工程数据板块专用附件上传
    :param project_id: 项目ID
    :param file: 上传文件
    :param file_type: 文件类型标签（如：施工图、质检报告、进度照片等）
    """
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
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id), "engineering")
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
        module=AttachmentModule.ENGINEERING,
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


@router.post("/{project_id}/finance/upload", response_model=AttachmentResponse)
async def upload_finance_attachment(
    project_id: UUID,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[Optional[str], Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
):
    """
    财务数据板块专用附件上传
    :param project_id: 项目ID
    :param file: 上传文件
    :param file_type: 文件类型标签（如：收款凭证、发票、财务报表等）
    """
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
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id), "finance")
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
        module=AttachmentModule.FINANCE,
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
