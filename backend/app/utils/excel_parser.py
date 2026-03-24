import pandas as pd
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from app.schemas.excel_schema import (
    ExcelImportResult,
    ExcelImportErrorItem,
    ProjectExcelImport,
    MarketDataExcelImport,
    EngineeringDataExcelImport,
    FinanceDataExcelImport
)
from app.schemas.project import ProjectCreate
from app.schemas.market import MarketDataCreate
from app.schemas.engineering import EngineeringDataCreate
from app.schemas.finance import FinanceDataCreate
from app.models.project import ProjectStatus

# 模块映射：支持扩展其他板块（如engineering/finance）
MODULE_EXCEL_MODEL_MAP = {
    "project": {
        "import_model": ProjectExcelImport,
        "create_model": ProjectCreate,
        "skip_header": True,  # Excel是否包含表头行
        "header_row": 0       # 表头行号（从0开始）
    },
    "market": {
        "import_model": MarketDataExcelImport,
        "create_model": MarketDataCreate,
        "skip_header": True,
        "header_row": 0
    },
    "engineering": {
        "import_model": EngineeringDataExcelImport,
        "create_model": EngineeringDataCreate,
        "skip_header": True,
        "header_row": 0
    },
    "finance": {
        "import_model": FinanceDataExcelImport,
        "create_model": FinanceDataCreate,
        "skip_header": True,
        "header_row": 0
    }
}

class ExcelParser:
    """通用Excel解析器（支持多模块导入解析）"""
    
    def __init__(self, module: str):
        """
        初始化解析器
        :param module: 模块名称（如project/engineering/finance）
        """
        if module not in MODULE_EXCEL_MODEL_MAP:
            raise ValueError(f"不支持的模块：{module}，仅支持{list(MODULE_EXCEL_MODEL_MAP.keys())}")
        self.module = module
        self.config = MODULE_EXCEL_MODEL_MAP[module]
        self.import_model: Type[BaseModel] = self.config["import_model"]
        self.create_model: Type[BaseModel] = self.config["create_model"]
        self.result = ExcelImportResult()
        # 缓存解析成功的创建模型实例
        self.valid_create_objs: List[BaseModel] = []
        # 缓存原始导入对象（用于后续提取项目编码等信息）
        self.import_objs: List[Dict[str, Any]] = []

    def parse_file(self, file_path: str, sheet_name: Optional[str] = None) -> ExcelImportResult:
        """
        解析本地Excel文件
        :param file_path: Excel文件绝对/相对路径
        :param sheet_name: 工作表名称（None则读取第一个工作表）
        :return: 解析结果（成功数/失败数/错误详情）
        """
        try:
            # 若sheet_name为None，指定读取第一个sheet
            if sheet_name is None:
                sheet_name = 0  # 读取第一个工作表
            
            # 读取Excel文件，统一按字符串解析避免类型异常
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=self.config["header_row"] if self.config["skip_header"] else None,
                dtype=str,
                engine="openpyxl"  # 显式指定引擎，兼容xlsx格式
            )
            
            # 确保df是DataFrame而非字典
            if isinstance(df, dict):
                # 如果返回字典，取第一个sheet
                df = list(df.values())[0]
            
            # 清理列名：去除前后空格（处理Excel导出时可能出现的空格问题）
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            
            # 清理空行、重置索引（保证行号连续）
            df = df.dropna(how="all").reset_index(drop=True)
            
            # 逐行解析数据
            for row_idx, row in df.iterrows():
                # Excel实际行号 = 索引+2（表头占1行，Excel行号从1开始）
                self._parse_row(row, row_idx + 2)
            
        except Exception as e:
            # 捕获文件读取类全局错误
            self.result.errors.append(
                ExcelImportErrorItem(
                    row=0,
                    field="全局",
                    message=f"文件解析失败：{str(e)}"
                )
            )
            self.result.fail_count = 1
        
        return self.result

    def parse_bytes(self, file_bytes: bytes, sheet_name: Optional[str] = None) -> ExcelImportResult:
        """
        解析Excel字节流（适配FastAPI UploadFile上传场景）
        :param file_bytes: Excel文件字节流
        :param sheet_name: 工作表名称（None则读取第一个工作表）
        :return: 解析结果
        """
        try:
            from io import BytesIO
            # 使用BytesIO包装字节流，pandas.read_excel需要file-like对象
            file_stream = BytesIO(file_bytes)
            
            # 若sheet_name为None，指定读取第一个sheet
            if sheet_name is None:
                sheet_name = 0  # 读取第一个工作表
            
            df = pd.read_excel(
                file_stream,
                sheet_name=sheet_name,
                header=self.config["header_row"] if self.config["skip_header"] else None,
                dtype=str,
                engine="openpyxl"
            )
            
            # 确保df是DataFrame而非字典
            if isinstance(df, dict):
                # 如果返回字典，取第一个sheet
                df = list(df.values())[0]
            
            # 清理列名：去除前后空格（处理Excel导出时可能出现的空格问题）
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            
            df = df.dropna(how="all").reset_index(drop=True)
            
            for row_idx, row in df.iterrows():
                self._parse_row(row, row_idx + 2)
            
        except Exception as e:
            self.result.errors.append(
                ExcelImportErrorItem(
                    row=0,
                    field="全局",
                    message=f"字节流解析失败：{str(e)}"
                )
            )
            self.result.fail_count = 1
        
        return self.result

    def _parse_row(self, row: pd.Series, excel_row: int):
        """
        解析单行Excel数据，完成校验和模型转换
        :param row: Pandas行数据
        :param excel_row: Excel中的实际行号（用于错误提示）
        """
        # 转换为字典并将空值替换为None，同时清理列名（去除前后空格）
        row_dict = {k.strip() if isinstance(k, str) else k: (v if pd.notna(v) else None) 
                    for k, v in row.items()}
        
        try:
            # 1. 校验Excel导入模型（字段格式/必填项等）
            import_obj = self.import_model(**row_dict)
            
            # 2. 转换为业务创建模型（如ProjectCreate）
            create_obj = self._convert_to_create_model(import_obj)
            
            # 3. 保存原始导入对象数据（用于后续提取项目编码等）
            self.import_objs.append(row_dict)
            
            # 4. 缓存有效数据、更新成功计数
            self.valid_create_objs.append(create_obj)
            self.result.success_count += 1
            
        except ValidationError as e:
            # Pydantic校验错误，逐字段记录错误信息
            for err in e.errors():
                field = err["loc"][0] if err["loc"] else "未知字段"
                field_cn = self._map_field_to_cn(field)
                self.result.errors.append(
                    ExcelImportErrorItem(
                        row=excel_row,
                        field=field_cn,
                        message=err["msg"]
                    )
                )
            self.result.fail_count += 1
        except Exception as e:
            # 其他未知解析错误
            self.result.errors.append(
                ExcelImportErrorItem(
                    row=excel_row,
                    field="全局",
                    message=f"行解析失败：{str(e)}"
                )
            )
            self.result.fail_count += 1

    def _convert_to_create_model(self, import_obj: BaseModel) -> BaseModel:
        """
        将Excel导入模型转换为业务创建模型（自动类型转换）
        :param import_obj: Excel导入模型实例
        :return: 业务创建模型实例
        """
        # 提取模型数据（所有模块都使用原始中文字段名）
        import_data = import_obj.model_dump()
        
        # 项目模块专属转换逻辑
        if self.module == "project":
            create_data = {
                "project_code": import_data.get("项目编码"),
                "project_name": import_data.get("项目名称"),
                "description": import_data.get("项目描述"),
                "construction_unit": import_data.get("建设单位"),
                "location": import_data.get("项目地点"),
                "contract_start_date": import_data.get("合同开始时间"),
                "contract_end_date": import_data.get("合同结束时间"),
                "contract_duration": self._convert_to_int(import_data.get("合同工期")),
                "actual_start_date": import_data.get("实际开工时间"),
                "status": import_data.get("项目状态") or ProjectStatus.PLANNING
            }
            # 过滤空值（避免传递None到非可选字段）
            create_data = {k: v for k, v in create_data.items() if v is not None}
            return self.create_model(**create_data)
        
        # 市场数据转换逻辑（从中文字段名映射）
        if self.module == "market":
            create_data = {
                "year": self._convert_to_int(import_data.get("年份")),
                "month": self._convert_to_int(import_data.get("月份")),
                "building_area": self._convert_to_decimal(import_data.get("建筑面积")),
                "structure": import_data.get("结构形式"),
                "floors": self._convert_to_int(import_data.get("层数")),
                "contract_value": self._convert_to_decimal(import_data.get("合同金额")),
                "prepayment_ratio": self._convert_to_decimal(import_data.get("预付款比例")),
                "advance_amount": self._convert_to_decimal(import_data.get("预付款金额")),
                "progress_payment_ratio": self._convert_to_decimal(import_data.get("进度款比例")),
                "contract_type": import_data.get("合同类型"),
                "remarks": import_data.get("备注")
            }
            create_data = {k: v for k, v in create_data.items() if v is not None}
            return self.create_model(**create_data)
        
        # 工程数据转换逻辑（从中文字段名映射）
        elif self.module == "engineering":
            create_data = {
                "year": self._convert_to_int(import_data.get("年份")),
                "month": self._convert_to_int(import_data.get("月份")),
                "actual_duration": self._convert_to_int(import_data.get("实际工期")),
                "end_period_progress": import_data.get("期末进度"),
                "contract_value": self._convert_to_decimal(import_data.get("合同金额")),
                "monthly_output": self._convert_to_decimal(import_data.get("月产值")),
                "planned_output": self._convert_to_decimal(import_data.get("计划产值")),
                "monthly_approval": self._convert_to_decimal(import_data.get("月批复")),
                "staff_count": self._convert_to_int(import_data.get("管理人员")),
                "next_month_plan": self._convert_to_decimal(import_data.get("下月计划")),
                "remarks": import_data.get("备注")
            }
            create_data = {k: v for k, v in create_data.items() if v is not None}
            return self.create_model(**create_data)
        
        # 财务数据转换逻辑（从中文字段名映射）
        elif self.module == "finance":
            create_data = {
                "year": self._convert_to_int(import_data.get("年份")),
                "month": self._convert_to_int(import_data.get("月份")),
                "monthly_revenue": self._convert_to_decimal(import_data.get("月营收")),
                "monthly_cost": self._convert_to_decimal(import_data.get("月成本")),
                "monthly_payment_received": self._convert_to_decimal(import_data.get("月回款")),
                "target_margin": self._convert_to_decimal(import_data.get("目标毛利率")),
                "remarks": import_data.get("备注")
            }
            create_data = {k: v for k, v in create_data.items() if v is not None}
            return self.create_model(**create_data)
        
        # 默认直接转换
        return self.create_model(**import_data)

    @staticmethod
    def _convert_to_int(value: Any) -> Optional[int]:
        """
        将值转换为整数（处理None和空字符串）
        """
        if value is None or value == "":
            return None
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _convert_to_decimal(value: Any) -> Optional[Any]:
        """
        将值转换为Decimal（处理None和空字符串）
        """
        if value is None or value == "":
            return None
        try:
            from decimal import Decimal
            return Decimal(str(value).strip())
        except (ValueError, TypeError):
            return None

    def _map_field_to_cn(self, field: str) -> str:
        """
        将英文字段名映射为中文表头（优化错误提示可读性）
        :param field: 英文字段名
        :return: 中文表头/字段名
        """
        # 从导入模型的字段信息中提取别名（中文）
        field_map = {
            field_name: field_info.alias or field_name
            for field_name, field_info in self.import_model.model_fields.items()
        }
        return field_map.get(field, field)

    def get_valid_data(self) -> List[BaseModel]:
        """
        获取解析成功的业务创建模型列表（用于后续入库）
        :return: 有效创建模型实例列表
        """
        return self.valid_create_objs

    def get_import_objs(self) -> List[Dict[str, Any]]:
        """
        获取原始导入对象数据（包含所有Excel字段，用于提取项目编码等）
        :return: 原始行数据字典列表
        """
        return self.import_objs

    def reset(self):
        """重置解析器状态（复用解析器时使用）"""
        self.result = ExcelImportResult()
        self.valid_create_objs = []
        self.import_objs = []

# ===================== 快捷调用函数（简化业务层使用） =====================
def parse_project_excel(file_path: str, sheet_name: Optional[str] = None) -> ExcelParser:
    """
    快捷解析项目Excel文件（本地文件）
    :param file_path: Excel文件路径
    :param sheet_name: 工作表名称
    :return: 解析器实例（可通过.get_valid_data()获取有效数据）
    """
    parser = ExcelParser(module="project")
    parser.parse_file(file_path, sheet_name)
    return parser

def parse_project_excel_bytes(file_bytes: bytes, sheet_name: Optional[str] = None) -> ExcelParser:
    """
    快捷解析项目Excel字节流（FastAPI上传场景）
    :param file_bytes: Excel文件字节流
    :param sheet_name: 工作表名称
    :return: 解析器实例
    """
    parser = ExcelParser(module="project")
    parser.parse_bytes(file_bytes, sheet_name)
    return parser