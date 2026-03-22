from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from app.models.project import ProjectStatus
from uuid import UUID

# ===================== 项目模块 Excel 导入模型 =====================
class ProjectExcelImport(BaseModel):
    """
    项目Excel导入模型（适配中文表头，含导入专属校验）
    """
    项目编码: str = Field(..., min_length=1, max_length=50)
    项目名称: str = Field(..., min_length=1, max_length=200)
    项目描述: Optional[str] = Field(None)
    建设单位: Optional[str] = Field(None)
    项目地点: Optional[str] = Field(None)
    合同开始时间: Optional[date] = Field(None)
    合同结束时间: Optional[date] = Field(None)
    合同工期: Optional[int] = Field(None, ge=1)
    实际开工时间: Optional[date] = Field(None)
    项目状态: Optional[str] = Field(None)

    # 校验1：合同结束时间不能早于开始时间
    @field_validator("合同结束时间")
    def validate_contract_date(cls, v, info: ValidationInfo):
        if v is None:
            return v
        start_date = info.data.get("合同开始时间")
        if start_date and v < start_date:
            raise ValueError("合同结束时间不能早于合同开始时间")
        return v

    # 校验2：项目状态值映射（Excel中输入中文，自动转枚举值）
    @field_validator("项目状态", mode="before")
    def map_status(cls, v):
        if not v:
            return ProjectStatus.PLANNING  # 默认为规划中
        # 中文状态转枚举值
        status_map = {
            "规划中": ProjectStatus.PLANNING,
            "进行中": ProjectStatus.IN_PROGRESS,
            "已完成": ProjectStatus.COMPLETED,
            "已暂停": ProjectStatus.SUSPENDED
        }
        if v not in status_map:
            raise ValueError(f"项目状态无效，仅支持：{list(status_map.keys())}")
        return status_map[v]

    model_config = {
        "strict": False,           # 兼容Excel单元格的类型转换（如数字转字符串）
        "validate_assignment": True  # 赋值时也触发校验
    }


# ===================== 项目模块 Excel 导出模型 =====================
class ProjectExcelExport(BaseModel):
    """
    项目Excel导出模型（用于将项目数据导出为Excel）
    """
    project_code: str = Field(..., description="项目编码")
    project_name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    construction_unit: Optional[str] = Field(None, description="建设单位")
    location: Optional[str] = Field(None, description="项目地点")
    contract_start_date: Optional[date] = Field(None, description="合同开始时间")
    contract_end_date: Optional[date] = Field(None, description="合同结束时间")
    contract_duration: Optional[int] = Field(None, description="合同工期")
    actual_start_date: Optional[date] = Field(None, description="实际开工时间")
    status: Optional[str] = Field(None, description="项目状态")

    model_config = {
        "from_attributes": True,
    }


# ===================== 市场数据 Excel 导入模型 =====================
class MarketDataExcelImport(BaseModel):
    """
    市场数据Excel导入模型（使用中文列名，与前端保持一致）
    """
    项目编码: str = Field(..., min_length=1, max_length=50, description="用于匹配数据库中的项目")
    年份: int = Field(..., ge=2000, le=2100)
    月份: int = Field(..., ge=1, le=12)
    建筑面积: Optional[str] = Field(None)
    结构形式: Optional[str] = Field(None)
    层数: Optional[str] = Field(None)
    合同金额: Optional[str] = Field(None)
    预付款比例: Optional[str] = Field(None)
    预付款金额: Optional[str] = Field(None)
    进度款比例: Optional[str] = Field(None)
    合同类型: Optional[str] = Field(None)
    备注: Optional[str] = Field(None)

    model_config = {
        "populate_by_name": True,
        "strict": False,
        "validate_assignment": True
    }


# ===================== 工程数据 Excel 导入模型 =====================
class EngineeringDataExcelImport(BaseModel):
    """
    工程数据Excel导入模型（使用中文列名，与前端保持一致）
    """
    项目编码: str = Field(..., min_length=1, max_length=50, description="用于匹配数据库中的项目")
    年份: int = Field(..., ge=2000, le=2100)
    月份: int = Field(..., ge=1, le=12)
    实际工期: Optional[str] = Field(None)
    期末进度: Optional[str] = Field(None)
    合同金额: Optional[str] = Field(None)
    月产值: Optional[str] = Field(None)
    计划产值: Optional[str] = Field(None)
    月批复: Optional[str] = Field(None)
    管理人员: Optional[str] = Field(None)
    下月计划: Optional[str] = Field(None)
    备注: Optional[str] = Field(None)

    model_config = {
        "populate_by_name": True,
        "strict": False,
        "validate_assignment": True
    }


# ===================== 财务数据 Excel 导入模型 =====================
class FinanceDataExcelImport(BaseModel):
    """
    财务数据Excel导入模型（使用中文列名，与前端保持一致）
    项目编码: str = Field(..., min_length=1, max_length=50, description="用于匹配数据库中的项目")
    """
    年份: int = Field(..., ge=2000, le=2100)
    月份: int = Field(..., ge=1, le=12)
    月营收: Optional[str] = Field(None)
    月成本: Optional[str] = Field(None)
    月回款: Optional[str] = Field(None)
    目标毛利率: Optional[str] = Field(None)
    备注: Optional[str] = Field(None)

    model_config = {
        "populate_by_name": True,
        "strict": False,
        "validate_assignment": True
    }


# ===================== Excel 导入通用返回模型 =====================
class ExcelImportErrorItem(BaseModel):
    """
    Excel导入错误项（记录行号+字段+原因）
    """
    row: int = Field(..., description="Excel中的行号（从1开始）")
    field: str = Field(..., description="错误字段（中文表头）")
    message: str = Field(..., description="错误原因")

class ExcelImportResult(BaseModel):
    """
    Excel导入结果汇总
    """
    success_count: int = Field(0, description="成功导入数量")
    fail_count: int = Field(0, description="失败数量")
    errors: List[ExcelImportErrorItem] = Field(default_factory=list, description="错误详情")
    