from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_active_user
from app.services.excel_service import ExcelService

router = APIRouter(prefix="/api/excel", tags=["excel"])


@router.post("/import/project", status_code=status.HTTP_200_OK)
async def import_project_excel(
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    导入项目数据（Excel列名需为中文，与前端表格保持一致）
    支持的列名（中文）：项目编码, 项目名称, 项目描述, 建设单位, 项目地点,
                      合同开始日期, 合同结束日期, 合同工期, 实际开工时间, 项目状态
    """
    excel_service = ExcelService(db)
    try:
        await excel_service.import_excel_to_project(
            project_id=None,
            file=file,
            user=current_user,
            data_type="project"
        )
        return {
            "status": "success",
            "message": "项目数据已成功导入"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"项目数据导入失败：{str(e)}"
        )
    finally:
        await file.close()


@router.post("/import/{project_id}", status_code=status.HTTP_200_OK)
async def import_excel_to_project(
    project_id: UUID,
    data_type: Annotated[str, Query(description="数据类型：market/engineering/finance")],
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    导入Excel数据到指定项目的对应板块（支持自动项目编码匹配）

    - **market** (市场数据): 年份, 月份, 建筑面积, 结构形式, 层数, 合同金额, 预付款比例, 预付款金额, 进度款比例, 合同类型, 备注
    - **engineering** (工程数据): 年份, 月份, 实际工期, 期末进度, 合同金额, 月产值, 计划产值, 月批复, 管理人员, 下月计划, 备注
    - **finance** (财务数据): 年份, 月份, 月营收, 月成本, 月回款, 目标毛利率, 备注
    """
    valid_data_types = ["market", "engineering", "finance"]
    if data_type not in valid_data_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的数据类型！仅支持：{','.join(valid_data_types)}"
        )

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
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel导入失败：{str(e)}"
        )
    finally:
        await file.close()


@router.post("/import/auto/data", status_code=status.HTTP_200_OK)
async def import_excel_auto_match_project(
    data_type: Annotated[str, Query(description="数据类型：market/engineering/finance")],
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    自动匹配项目编码导入Excel数据（不需要指定project_id）

    Excel中必须包含'项目编码'列，系统将自动查询数据库并将数据关联到对应项目
    """
    valid_data_types = ["market", "engineering", "finance"]
    if data_type not in valid_data_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的数据类型！仅支持：{','.join(valid_data_types)}"
        )

    excel_service = ExcelService(db)
    try:
        await excel_service.import_excel_to_project(
            project_id=None,
            file=file,
            user=current_user,
            data_type=data_type
        )
        return {
            "status": "success",
            "message": f"Excel数据已根据项目编码自动匹配并导入{data_type}板块",
            "data_type": data_type
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动匹配导入失败：{str(e)}"
        )
    finally:
        await file.close()
