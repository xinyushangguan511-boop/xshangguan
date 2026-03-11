import pandas as pd
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from app.schemas.excel_schema import (
    ExcelImportResult,
    ExcelImportErrorItem,
    ProjectExcelImport
)
from app.schemas.project import ProjectCreate
from app.models.project import ProjectStatus

# 模块映射：支持扩展其他板块（如engineering/finance）
MODULE_EXCEL_MODEL_MAP = {
    "project": {
        "import_model": ProjectExcelImport,
        "create_model": ProjectCreate,
        "skip_header": True,  # Excel是否包含表头行
        "header_row": 0       # 表头行号（从0开始）
    },
    # 可扩展其他模块示例
    # "engineering": {
    #     "import_model": EngineeringExcelImport,
    #     "create_model": EngineeringCreate,
    #     "skip_header": True,
    #     "header_row": 0
    # }
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

    def parse_file(self, file_path: str, sheet_name: Optional[str] = None) -> ExcelImportResult:
        """
        解析本地Excel文件
        :param file_path: Excel文件绝对/相对路径
        :param sheet_name: 工作表名称（None则读取第一个工作表）
        :return: 解析结果（成功数/失败数/错误详情）
        """
        try:
            # 读取Excel文件，统一按字符串解析避免类型异常
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=self.config["header_row"] if self.config["skip_header"] else None,
                dtype=str,
                engine="openpyxl"  # 显式指定引擎，兼容xlsx格式
            )
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
        :param sheet_name: 工作表名称
        :return: 解析结果
        """
        try:
            df = pd.read_excel(
                file_bytes,
                sheet_name=sheet_name,
                header=self.config["header_row"] if self.config["skip_header"] else None,
                dtype=str,
                engine="openpyxl"
            )
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
        # 转换为字典并将空值替换为None
        row_dict = row.fillna(None).to_dict()
        
        try:
            # 1. 校验Excel导入模型（字段格式/必填项等）
            import_obj = self.import_model(**row_dict)
            
            # 2. 转换为业务创建模型（如ProjectCreate）
            create_obj = self._convert_to_create_model(import_obj)
            
            # 3. 缓存有效数据、更新成功计数
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
        将Excel导入模型转换为业务创建模型
        :param import_obj: Excel导入模型实例
        :return: 业务创建模型实例
        """
        # 提取模型数据（支持别名映射）
        import_data = import_obj.model_dump(by_alias=True)
        
        # 项目模块专属转换逻辑
        if self.module == "project":
            create_data = {
                "project_code": import_data.get("project_code"),
                "project_name": import_data.get("project_name"),
                "description": import_data.get("description"),
                "construction_unit": import_data.get("construction_unit"),
                "location": import_data.get("location"),
                "contract_start_date": import_data.get("contract_start_date"),
                "contract_end_date": import_data.get("contract_end_date"),
                "contract_duration": import_data.get("contract_duration"),
                "actual_start_date": import_data.get("actual_start_date"),
                "status": import_data.get("status") or ProjectStatus.PLANNING
            }
            # 过滤空值（避免传递None到非可选字段）
            create_data = {k: v for k, v in create_data.items() if v is not None}
            return self.create_model(**create_data)
        
        # 其他模块转换逻辑可在此扩展
        # elif self.module == "engineering":
        #     create_data = {...}
        #     return self.create_model(**create_data)
        
        # 默认直接转换
        return self.create_model(**import_data)

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

    def reset(self):
        """重置解析器状态（复用解析器时使用）"""
        self.result = ExcelImportResult()
        self.valid_create_objs = []

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