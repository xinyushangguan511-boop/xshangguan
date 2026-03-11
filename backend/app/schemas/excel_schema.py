from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.project import ProjectStatus
from uuid import UUID

# ===================== 项目模块 Excel 导入模型 =====================
class ProjectExcelImport(BaseModel):
    """
    项目Excel导入模型（适配中文表头，含导入专属校验）
    """
    项目编码: str = Field(..., alias="project_code", min_length=1, max_length=50)
    项目名称: str = Field(..., alias="project_name", min_length=1, max_length=200)
    项目描述: Optional[str] = Field(None, alias="description")
    建设单位: Optional[str] = Field(None, alias="construction_unit")
    项目地点: Optional[str] = Field(None, alias="location")
    合同开始时间: Optional[date] = Field(None, alias="contract_start_date")
    合同结束时间: Optional[date] = Field(None, alias="contract_end_date")
    合同工期: Optional[int] = Field(None, alias="contract_duration", ge=1)
    实际开工时间: Optional[date] = Field(None, alias="actual_start_date")
    项目状态: Optional[str] = Field(None, alias="status")

    # 校验1：合同结束时间不能早于开始时间
    @field_validator("合同结束时间")
    def validate_contract_date(cls, v, values):
        start_date = values.data.get("合同开始时间")
        if start_date and v and v < start_date:
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
        "populate_by_name": True,  # 支持按别名（project_code）赋值
        "strict": False,           # 兼容Excel单元格的类型转换（如数字转字符串）
        "validate_assignment": True  # 赋值时也触发校验
    }

# ===================== 项目模块 Excel 导出模型 =====================
class ProjectExcelExport(BaseModel):
    """
    项目Excel导出模型（格式化字段为中文展示）
    """
    项目编码: str = Field(..., alias="project_code")
    项目名称: str = Field(..., alias="project_name")
    项目描述: Optional[str] = Field(None, alias="description")
    建设单位: Optional[str] = Field(None, alias="construction_unit")
    项目地点: Optional[str] = Field(None, alias="location")
    合同开始时间: Optional[str] = Field(None, alias="contract_start_date")
    合同结束时间: Optional[str] = Field(None, alias="contract_end_date")
    合同工期: Optional[int] = Field(None, alias="contract_duration")
    实际开工时间: Optional[str] = Field(None, alias="actual_start_date")
    项目状态: str = Field(..., alias="status")
    创建人ID: UUID = Field(..., alias="created_by")
    创建时间: str = Field(..., alias="created_at")
    更新时间: str = Field(..., alias="updated_at")

    # 格式化日期字段（date/datetime → 字符串 YYYY-MM-DD）
    @field_validator("合同开始时间", "合同结束时间", "实际开工时间", mode="before")
    def format_date(cls, v):
        if isinstance(v, (date, datetime)):
            return v.strftime("%Y-%m-%d")
        return v

    # 修复：校验字段名改为中文「项目状态」（而非alias「status」）
    @field_validator("项目状态", mode="before")
    def format_status(cls, v):
        status_map = {
            ProjectStatus.PLANNING: "规划中",
            ProjectStatus.IN_PROGRESS: "进行中",
            ProjectStatus.COMPLETED: "已完成",
            ProjectStatus.SUSPENDED: "已暂停"
        }
        return status_map.get(v, str(v))

    # 修复：校验字段名改为中文「创建时间」「更新时间」（而非alias）
    @field_validator("创建时间", "更新时间", mode="before")
    def format_datetime(cls, v):
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v

    model_config = {
        "populate_by_name": True,
        "from_attributes": True  # 支持从ORM模型（如SQLAlchemy）直接赋值
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
    