from typing import List, Optional, Dict, Any
from uuid import UUID
import pandas as pd
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

# 导入项目配置（核心：复用config.py中的全局配置）
from app.config import settings

# 导入项目模型和工具类
from app.models.project import Project
from app.models.user import User
from app.utils.file_utils import FileUtils  # 保留原工具类依赖


class ExcelService:
    """Excel处理服务（适配项目多板块：市场/工程/财务，复用全局配置）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 从全局配置读取Excel相关限制（统一配置源）
        self.allowed_excel_ext = {ext.lstrip(".") for ext in settings.ALLOWED_EXTENSIONS if ext in [".xls", ".xlsx"]}
        self.max_excel_size = settings.MAX_FILE_SIZE  # 复用全局文件大小限制

    async def validate_excel_file(self, file: UploadFile) -> bytes:
        """
        校验Excel文件（后缀+大小），并返回文件字节内容
        :param file: 上传的Excel文件
        :return: 文件字节内容
        :raise HTTPException: 校验失败时抛出
        """
        # 1. 校验文件后缀（仅保留Excel相关后缀）
        if not FileUtils.validate_file_extension(file.filename, self.allowed_excel_ext):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的Excel格式！仅允许：{','.join(self.allowed_excel_ext)}"
            )

        # 2. 读取文件内容并校验大小（复用全局MAX_FILE_SIZE）
        content = await file.read()
        if not FileUtils.validate_file_size(content, self.max_excel_size):
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件过大！最大允许：{self.max_excel_size / 1024 / 1024:.2f}MB"
            )

        await file.seek(0)  # 重置文件指针，兼容后续操作
        return content

    def parse_excel_to_dict(self, content: bytes, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        解析Excel内容为字典列表（适配多sheet：market/engineering/finance）
        :param content: Excel文件字节内容
        :param sheet_name: 指定sheet名（None则读取第一个sheet）
        :return: 解析后的字典列表
        :raise HTTPException: 解析失败时抛出
        """
        try:
            df = pd.read_excel(content, sheet_name=sheet_name)
            # 处理空值、统一字段名（小写+去空格）
            df = df.fillna("").rename(columns=lambda x: x.strip().lower())
            return df.to_dict("records")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Excel解析失败：{str(e)}"
            )

    async def import_excel_to_project(
        self,
        project_id: UUID,
        file: UploadFile,
        user: User,
        data_type: str  # "market"/"engineering"/"finance"
    ) -> Project:
        """
        将Excel数据导入指定项目的对应板块
        :param project_id: 项目ID
        :param file: 上传的Excel文件
        :param user: 当前操作用户（校验权限）
        :param data_type: 数据类型（对应项目的不同板块）
        :return: 更新后的项目对象
        :raise HTTPException: 权限不足/数据异常时抛出
        """
        # 1. 导入ProjectService并校验权限（避免循环导入，延迟导入）
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        # 校验项目存在性
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 校验编辑权限
        if not await project_service.can_edit_project(user, project):
            raise HTTPException(status_code=403, detail="无权限编辑该项目")

        # 2. 校验并读取Excel文件
        content = await self.validate_excel_file(file)
        excel_data = self.parse_excel_to_dict(content)
        if not excel_data:
            raise HTTPException(status_code=400, detail="Excel文件无有效数据")

        # 3. 根据数据类型导入对应板块
        if data_type == "market":
            await self._import_market_data(project, excel_data, user)
        elif data_type == "engineering":
            await self._import_engineering_data(project, excel_data, user)
        elif data_type == "finance":
            await self._import_finance_data(project, excel_data, user)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据类型：{data_type}")

        # 4. 提交并刷新项目
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def _import_market_data(self, project: Project, data: List[Dict[str, Any]], user: User):
        """导入市场板块数据（内部方法）"""
        # 清空原有数据（可选：根据业务需求调整为追加/覆盖）
        if project.market_data:
            await self.db.delete(project.market_data)
        
        # 解析Excel数据为MarketData模型（适配实际字段）
        first_row = data[0]
        market_data = MarketData(
            project_id=project.id,
            customer_name=first_row.get("customer_name", ""),
            contract_amount=float(first_row.get("contract_amount", 0.0)),
            sign_date=first_row.get("sign_date", None),
            updated_by=user.id
        )
        self.db.add(market_data)
        project.market_data = market_data

    async def _import_engineering_data(self, project: Project, data: List[Dict[str, Any]], user: User):
        """导入工程板块数据（内部方法）"""
        if project.engineering_data:
            await self.db.delete(project.engineering_data)
        
        first_row = data[0]
        engineering_data = EngineeringData(
            project_id=project.id,
            construction_progress=int(first_row.get("construction_progress", 0)),
            start_date=first_row.get("start_date", None),
            expected_end_date=first_row.get("expected_end_date", None),
            updated_by=user.id
        )
        self.db.add(engineering_data)
        project.engineering_data = engineering_data

    async def _import_finance_data(self, project: Project, data: List[Dict[str, Any]], user: User):
        """导入财务板块数据（内部方法）"""
        if project.finance_data:
            await self.db.delete(project.finance_data)
        
        first_row = data[0]
        finance_data = FinanceData(
            project_id=project.id,
            payment_received=float(first_row.get("payment_received", 0.0)),
            cost=float(first_row.get("cost", 0.0)),
            profit=float(first_row.get("profit", 0.0)),
            updated_by=user.id
        )
        self.db.add(finance_data)
        project.finance_data = finance_data

    async def export_project_to_excel(self, project_id: UUID, user: User) -> bytes:
        """
        导出项目多板块数据为Excel文件（bytes格式，供下载）
        :param project_id: 项目ID
        :param user: 当前操作用户（校验权限）
        :return: Excel文件字节内容
        :raise HTTPException: 权限不足/项目不存在时抛出
        """
        # 1. 校验权限和项目存在性
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        if not await project_service.can_access_project(user, project):
            raise HTTPException(status_code=403, detail="无权限访问该项目")

        # 2. 组装多板块数据（适配多sheet导出）
        excel_sheets = {
            "market": self._assemble_market_sheet(project),
            "engineering": self._assemble_engineering_sheet(project),
            "finance": self._assemble_finance_sheet(project)
        }

        # 3. 生成Excel文件（bytes格式，支持下载）
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for sheet_name, sheet_data in excel_sheets.items():
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            return output.getvalue()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Excel导出失败：{str(e)}"
            )

    def _assemble_market_sheet(self, project: Project) -> List[Dict[str, Any]]:
        """组装市场板块导出数据"""
        market_data = project.market_data or {}
        return [
            {
                "项目编号": project.project_code,
                "项目名称": project.project_name,
                "客户名称": market_data.customer_name if market_data else "",
                "合同金额": market_data.contract_amount if market_data else 0.0,
                "签约日期": market_data.sign_date.strftime("%Y-%m-%d") if (market_data and market_data.sign_date) else "",
                "创建人": project.created_by,
                "更新时间": project.updated_at.strftime("%Y-%m-%d %H:%M:%S") if project.updated_at else ""
            }
        ]

    def _assemble_engineering_sheet(self, project: Project) -> List[Dict[str, Any]]:
        """组装工程板块导出数据"""
        engineering_data = project.engineering_data or {}
        return [
            {
                "项目编号": project.project_code,
                "项目名称": project.project_name,
                "施工进度(%)": engineering_data.construction_progress if engineering_data else 0,
                "开工日期": engineering_data.start_date.strftime("%Y-%m-%d") if (engineering_data and engineering_data.start_date) else "",
                "预计完工日期": engineering_data.expected_end_date.strftime("%Y-%m-%d") if (engineering_data and engineering_data.expected_end_date) else "",
                "项目状态": project.status.value if hasattr(project.status, "value") else project.status,
                "更新时间": project.updated_at.strftime("%Y-%m-%d %H:%M:%S") if project.updated_at else ""
            }
        ]

    def _assemble_finance_sheet(self, project: Project) -> List[Dict[str, Any]]:
        """组装财务板块导出数据"""
        finance_data = project.finance_data or {}
        return [
            {
                "项目编号": project.project_code,
                "项目名称": project.project_name,
                "已收款金额": finance_data.payment_received if finance_data else 0.0,
                "成本": finance_data.cost if finance_data else 0.0,
                "利润": finance_data.profit if finance_data else 0.0,
                "更新时间": project.updated_at.strftime("%Y-%m-%d %H:%M:%S") if project.updated_at else ""
            }
        ]