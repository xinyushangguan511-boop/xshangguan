from typing import Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.project import Project
from app.models.user import User
from app.models.market import MarketData
from app.models.engineering import EngineeringData
from app.models.finance import FinanceData
from app.utils.file_utils import FileUtils
from app.utils.excel_parser import ExcelParser


class ExcelService:
    """Excel处理服务（适配项目多板块：市场/工程/财务，自动列名映射）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.allowed_excel_ext = [ext for ext in settings.ALLOWED_EXTENSIONS if ext in [".xls", ".xlsx"]]
        self.max_excel_size = settings.MAX_FILE_SIZE

    async def validate_excel_file(self, file: UploadFile) -> bytes:
        """校验Excel文件（后缀+大小），并返回文件字节内容"""
        if not FileUtils.validate_file_extension(file.filename, self.allowed_excel_ext):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的Excel格式！仅允许：{', '.join(self.allowed_excel_ext)}"
            )

        content = await file.read()
        if not FileUtils.validate_file_size(content, self.max_excel_size):
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件过大！最大允许：{self.max_excel_size / 1024 / 1024:.2f}MB"
            )

        await file.seek(0)
        return content

    async def import_excel_to_project(
        self,
        project_id: Optional[UUID],
        file: UploadFile,
        user: User,
        data_type: str
    ) -> Project:
        """将Excel数据导入指定项目的对应板块"""
        # project模块：直接处理，不关联project_id
        if data_type == "project":
            await self._import_project_data(file, user)
            return await self._get_dummy_project()

        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)

        # 校验并读取Excel文件
        content = await self.validate_excel_file(file)

        # 根据数据类型使用ExcelParser解析并导入
        if data_type == "market":
            await self._import_market_data_v2(project_id, content, user)
        elif data_type == "engineering":
            await self._import_engineering_data_v2(project_id, content, user)
        elif data_type == "finance":
            await self._import_finance_data_v2(project_id, content, user)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据类型：{data_type}")

        await self.db.commit()

        # 如果指定了project_id，则返回该项目对象；否则返回虚拟对象
        if project_id:
            project = await project_service.get_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")

            if not await project_service.can_edit_project(user, project):
                raise HTTPException(status_code=403, detail="无权限编辑该项目")

            await self.db.refresh(project)
            return project
        else:
            return await self._get_dummy_project()

    async def _import_project_data(self, file: UploadFile, user: User):
        """导入项目数据（按数据库列名自动映射）"""
        from app.services.project_service import ProjectService

        content = await self.validate_excel_file(file)

        parser = ExcelParser(module="project")
        result = parser.parse_bytes(content)

        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")

        valid_projects = parser.get_valid_data()
        project_service = ProjectService(self.db)

        for project_data in valid_projects:
            await project_service.create_project(project_data, user)

    async def _get_dummy_project(self) -> Project:
        """返回虚拟项目对象（用于project导入）"""
        dummy_project = Project(
            id=UUID(int=0),
            project_code="DUMMY",
            project_name="Project Import",
            created_by=UUID(int=0)
        )
        return dummy_project

    async def _import_market_data_v2(self, project_id: Optional[UUID], content: bytes, user: User):
        """导入市场数据（自动匹配项目编码并映射project_id）"""
        parser = ExcelParser(module="market")
        result = parser.parse_bytes(content)

        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")

        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()

        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)

        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )

        for idx, data_obj in enumerate(valid_data):
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")

            actual_project_id = project_id
            if project_code:
                matched_project = await project_service.get_by_code(project_code)
                if not matched_project:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Excel第{idx+2}行：项目编码'{project_code}'在数据库中不存在"
                    )
                actual_project_id = matched_project.id
            elif project_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )

            data_dict = data_obj.model_dump()
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}

            record = MarketData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)

    async def _import_engineering_data_v2(self, project_id: Optional[UUID], content: bytes, user: User):
        """导入工程数据（自动匹配项目编码并映射project_id）"""
        parser = ExcelParser(module="engineering")
        result = parser.parse_bytes(content)

        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")

        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()

        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)

        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )

        for idx, data_obj in enumerate(valid_data):
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")

            actual_project_id = project_id
            if project_code:
                matched_project = await project_service.get_by_code(project_code)
                if not matched_project:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Excel第{idx+2}行：项目编码'{project_code}'在数据库中不存在"
                    )
                actual_project_id = matched_project.id
            elif project_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )

            data_dict = data_obj.model_dump()
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}

            record = EngineeringData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)

    async def _import_finance_data_v2(self, project_id: Optional[UUID], content: bytes, user: User):
        """导入财务数据（自动匹配项目编码并映射project_id）"""
        parser = ExcelParser(module="finance")
        result = parser.parse_bytes(content)

        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")

        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()

        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)

        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )

        for idx, data_obj in enumerate(valid_data):
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")

            actual_project_id = project_id
            if project_code:
                matched_project = await project_service.get_by_code(project_code)
                if not matched_project:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Excel第{idx+2}行：项目编码'{project_code}'在数据库中不存在"
                    )
                actual_project_id = matched_project.id
            elif project_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )

            data_dict = data_obj.model_dump()
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}

            record = FinanceData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)
