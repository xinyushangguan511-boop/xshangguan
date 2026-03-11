from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

# 项目内部依赖
from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_active_user
from app.services.excel_service import ExcelService  # 导入Excel处理服务

# 初始化路由（前缀/tags与项目路由保持统一规范）
router = APIRouter(prefix="/api/excel", tags=["excel"])


@router.post("/import/{project_id}", status_code=status.HTTP_200_OK)
async def import_excel_to_project(
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    导入Excel数据到指定项目的对应板块
    :param project_id: 项目ID
    :param data_type: 数据类型（market/engineering/finance）
    :param file: 上传的Excel文件（仅支持.xls/.xlsx）
    :param db: 数据库会话
    :param current_user: 当前登录用户（已校验活跃状态）
    :return: 导入成功提示+项目信息
    """
    # 校验数据类型合法性
    valid_data_types = ["market", "engineering", "finance"]
    if data_type not in valid_data_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的数据类型！仅支持：{','.join(valid_data_types)}"
        )

    # 初始化Excel服务并执行导入
    excel_service = ExcelService(db)
    try:
        project = await excel_service.import_excel_to_project(
            project_id=project_id,
            file=file,
            user=current_user,
            data_type=data_type
        )
        return {
            "status": "success",
            "message": f"Excel数据已成功导入【{project.project_name}】的{data_type}板块",
            "project_id": str(project.id),
            "project_name": project.project_name
        }
    except HTTPException as e:
        # 透传ExcelService中抛出的业务异常
        raise e
    except Exception as e:
        # 捕获未知异常，返回通用错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel导入失败：{str(e)}"
        )


@router.get("/export/{project_id}", response_class=StreamingResponse)
async def export_project_to_excel(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    导出指定项目的所有板块数据为Excel文件（多sheet）
    :param project_id: 项目ID
    :param db: 数据库会话
    :param current_user: 当前登录用户（已校验活跃状态）
    :return: 流式Excel文件响应（直接下载）
    """
    # 初始化Excel服务并执行导出
    excel_service = ExcelService(db)
    try:
        # 获取Excel字节内容
        excel_bytes = await excel_service.export_project_to_excel(
            project_id=project_id,
            user=current_user
        )

        # 构造流式响应（支持浏览器直接下载）
        return StreamingResponse(
            content=BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=项目{project_id}_数据导出.xlsx",
                "Cache-Control": "no-cache"
            }
        )
    except HTTPException as e:
        # 透传权限/项目不存在等业务异常
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel导出失败：{str(e)}"

        )
