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
from app.models.market import MarketData
from app.models.engineering import EngineeringData
from app.models.finance import FinanceData
from app.utils.file_utils import FileUtils  # 保留原工具类依赖
from app.utils.excel_parser import ExcelParser  # 使用Excel解析器


class ExcelService:
    """Excel处理服务（适配项目多板块：市场/工程/财务，自动列名映射）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # 从全局配置读取Excel相关限制（统一配置源）
        # 注意：保留扩展名的点（.），与FileUtils.validate_file_extension的比对格式一致
        self.allowed_excel_ext = [ext for ext in settings.ALLOWED_EXTENSIONS if ext in [".xls", ".xlsx"]]
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
                detail=f"不支持的Excel格式！仅允许：{', '.join(self.allowed_excel_ext)}"
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

    async def import_excel_to_project(
        self,
        project_id: Optional[UUID],
        file: UploadFile,
        user: User,
        data_type: str  # "market"/"engineering"/"finance"/"project"
    ) -> Project:
        """
        将Excel数据导入指定项目的对应板块（自动按列名映射录入）
        
        :param project_id: 项目ID（当为None时表示自动匹配模式，依靠Excel中的项目编码）
        :param file: 上传的Excel文件
        :param user: 当前操作用户（校验权限）
        :param data_type: 数据类型（对应项目的不同板块）
        :return: 更新后的项目对象/导入结果
        :raise HTTPException: 权限不足/数据异常时抛出
        """
        # 1. project模块：直接处理，不关联project_id
        if data_type == "project":
            await self._import_project_data(file, user)
            # 返回一个虚拟project对象（project模块导入不关联project_id）
            return await self._get_dummy_project()
        
        # 2. 导入ProjectService并校验权限（避免循环导入，延迟导入）
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        # 3. 校验并读取Excel文件
        content = await self.validate_excel_file(file)
        
        # 4. 根据数据类型使用ExcelParser解析并导入
        if data_type == "market":
            await self._import_market_data_v2(project_id, content, user)
        elif data_type == "engineering":
            await self._import_engineering_data_v2(project_id, content, user)
        elif data_type == "finance":
            await self._import_finance_data_v2(project_id, content, user)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据类型：{data_type}")

        # 5. 提交数据库变更
        await self.db.commit()
        
        # 6. 如果指定了project_id，则返回该项目对象；否则返回虚拟对象
        if project_id:
            project = await project_service.get_by_id(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
            
            # 校验编辑权限
            if not await project_service.can_edit_project(user, project):
                raise HTTPException(status_code=403, detail="无权限编辑该项目")
            
            await self.db.refresh(project)
            return project
        else:
            # 自动匹配模式，返回虚拟对象
            return await self._get_dummy_project()

    async def _import_project_data(self, file: UploadFile, user: User):
        """
        导入项目数据（按数据库列名自动映射）
        """
        from app.services.project_service import ProjectService
        from app.schemas.project import ProjectCreate
        
        content = await self.validate_excel_file(file)
        
        # 使用ExcelParser解析项目数据
        parser = ExcelParser(module="project")
        result = parser.parse_bytes(content)
        
        # 检查是否有解析错误
        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")
        
        # 获取有效的项目创建数据
        valid_projects = parser.get_valid_data()
        
        project_service = ProjectService(self.db)
        
        # 批量创建项目
        for project_data in valid_projects:
            # project_data已经是ProjectCreate对象
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
        """
        导入市场数据（自动匹配项目编码并映射project_id）
        """
        parser = ExcelParser(module="market")
        result = parser.parse_bytes(content)
        
        # 检查是否有解析错误
        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")
        
        # 获取有效的市场数据创建对象和原始导入数据
        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()
        
        # 导入ProjectService进行项目查询
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        # 如果project_id为None，则必须从Excel中读取项目编码（自动匹配模式）
        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )
        
        # 批量创建市场数据记录
        for idx, data_obj in enumerate(valid_data):
            # 尝试从原始数据中获取项目编码
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")
            
            # 根据项目编码查询project_id（优先使用Excel中的编码）
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
                # 自动匹配模式但没有项目编码
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )
            
            data_dict = data_obj.model_dump()
            # 移除Excel特有字段（如果有）
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}
            
            record = MarketData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)

    async def _import_engineering_data_v2(self, project_id: Optional[UUID], content: bytes, user: User):
        """
        导入工程数据（自动匹配项目编码并映射project_id）
        """
        parser = ExcelParser(module="engineering")
        result = parser.parse_bytes(content)
        
        # 检查是否有解析错误
        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")
        
        # 获取有效的工程数据创建对象和原始导入数据
        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()
        
        # 导入ProjectService进行项目查询
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        # 如果project_id为None，则必须从Excel中读取项目编码（自动匹配模式）
        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )
        
        # 批量创建工程数据记录
        for idx, data_obj in enumerate(valid_data):
            # 尝试从原始数据中获取项目编码
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")
            
            # 根据项目编码查询project_id（优先使用Excel中的编码）
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
                # 自动匹配模式但没有项目编码
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )
            
            data_dict = data_obj.model_dump()
            # 移除Excel特有字段（如果有）
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}
            
            record = EngineeringData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)

    async def _import_finance_data_v2(self, project_id: Optional[UUID], content: bytes, user: User):
        """
        导入财务数据（自动匹配项目编码并映射project_id）
        """
        parser = ExcelParser(module="finance")
        result = parser.parse_bytes(content)
        
        # 检查是否有解析错误
        if result.fail_count > 0 and not parser.get_valid_data():
            error_msg = "\n".join([f"第{e.row}行 {e.field}：{e.message}" for e in result.errors[:5]])
            raise HTTPException(status_code=400, detail=f"Excel解析失败：\n{error_msg}")
        
        # 获取有效的财务数据创建对象和原始导入数据
        valid_data = parser.get_valid_data()
        import_objs = parser.get_import_objs()
        
        # 导入ProjectService进行项目查询
        from app.services.project_service import ProjectService
        project_service = ProjectService(self.db)
        
        # 如果project_id为None，则必须从Excel中读取项目编码（自动匹配模式）
        if project_id is None:
            for idx, import_obj in enumerate(import_objs):
                project_code = import_obj.get("项目编码")
                if not project_code:
                    raise HTTPException(
                        status_code=400,
                        detail=f"自动匹配模式下，Excel中每一行都必须包含项目编码，第{idx+2}行缺失项目编码"
                    )
        
        # 批量创建财务数据记录
        for idx, data_obj in enumerate(valid_data):
            # 尝试从原始数据中获取项目编码
            import_obj = import_objs[idx] if idx < len(import_objs) else {}
            project_code = import_obj.get("项目编码")
            
            # 根据项目编码查询project_id（优先使用Excel中的编码）
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
                # 自动匹配模式但没有项目编码
                raise HTTPException(
                    status_code=400,
                    detail=f"自动匹配模式下，第{idx+2}行必须包含项目编码"
                )
            
            data_dict = data_obj.model_dump()
            # 移除Excel特有字段（如果有）
            data_dict = {k: v for k, v in data_dict.items() if not k.startswith("_")}
            
            record = FinanceData(
                project_id=actual_project_id,
                created_by=user.id,
                **data_dict
            )
            self.db.add(record)
