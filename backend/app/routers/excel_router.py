from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
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
    
    示例Excel列名：
    | 项目编码 | 项目名称 | 建设单位 | 项目地点 | ...
    
    :param file: 上传的Excel文件
    :param db: 数据库会话
    :param current_user: 当前登录用户（已校验活跃状态）
    :return: 导入成功提示
    """
    # Excel导入走“内存解析+入库”链路，不走附件落盘。
    excel_service = ExcelService(db)
    try:
        await excel_service.import_excel_to_project(
            project_id=UUID(int=0),  # 项目导入不需要project_id
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
        # 无论成功失败都关闭UploadFile，避免Windows下临时文件句柄占用。
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
    
    **项目匹配方式**：
    1. 如果Excel中包含'项目编码'列，系统将自动在数据库中查询并匹配对应的项目ID
    2. 如果Excel中没有'项目编码'列，则使用URL路径参数中的project_id
    
    - **market** (市场数据): 项目编码(可选), 年份, 月份, 建筑面积, 结构形式, 层数, 合同金额, 预付款比例, 预付款金额, 进度款比例, 合同类型, 备注
    - **engineering** (工程数据): 项目编码(可选), 年份, 月份, 实际工期, 期末进度, 合同金额, 月产值, 计划产值, 月批复, 管理人员, 下月计划, 备注
    - **finance** (财务数据): 项目编码(可选), 年份, 月份, 月营收, 月成本, 月回款, 目标毛利率, 备注
    
    示例Excel列名（市场数据）：
    | 项目编码 | 年份 | 月份 | 建筑面积 | 结构形式 | 层数 | 合同金额 | ...
    
    :param project_id: 项目ID（当Excel中没有项目编码列时使用此参数）
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

    # 初始化Excel服务并执行导入。
    # 该分支允许“指定项目导入”，也允许Excel中自带项目编码时自动覆盖project_id。
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
    finally:
        # 无论导入是否报错，都释放上传文件资源。
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
    
    **支持的数据类型**：
    - **market** (市场数据): 项目编码(必填), 年份, 月份, 建筑面积, 结构形式, 层数, 合同金额, 预付款比例, 预付款金额, 进度款比例, 合同类型, 备注
    - **engineering** (工程数据): 项目编码(必填), 年份, 月份, 实际工期, 期末进度, 合同金额, 月产值, 计划产值, 月批复, 管理人员, 下月计划, 备注
    - **finance** (财务数据): 项目编码(必填), 年份, 月份, 月营收, 月成本, 月回款, 目标毛利率, 备注
    
    **Excel示例（市场数据）**：
    | 项目编码 | 年份 | 月份 | 建筑面积 | 结构形式 | 层数 | 合同金额 | ...
    | P001     | 2024 | 1    | 5000   | 框架   | 20   | 100000  | ...
    | P002     | 2024 | 1    | 8000   | 钢混   | 25   | 150000  | ...
    
    :param data_type: 数据类型（market/engineering/finance）
    :param file: 上传的Excel文件（仅支持.xls/.xlsx）
    :param db: 数据库会话
    :param current_user: 当前登录用户（已校验活跃状态）
    :return: 导入成功提示+导入统计信息
    """
    # 校验数据类型合法性
    valid_data_types = ["market", "engineering", "finance"]
    if data_type not in valid_data_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的数据类型！仅支持：{','.join(valid_data_types)}"
        )

    # 自动匹配模式：完全依赖Excel中的“项目编码”列进行项目定位。
    excel_service = ExcelService(db)
    try:
        # project_id传None作为信号：仅按项目编码匹配，不接受外部项目ID兜底。
        result = await excel_service.import_excel_to_project(
            project_id=None,  # 信号：完全依靠项目编码匹配
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
        # 透传ExcelService中抛出的业务异常
        raise e
    except Exception as e:
        # 捕获未知异常，返回通用错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动匹配导入失败：{str(e)}"
        )
    finally:
        # 无论成功失败都关闭UploadFile，防止临时文件长期占用。
        await file.close()
