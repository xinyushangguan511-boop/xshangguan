from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.project import Project
from app.models.user import User, Department
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.market_data),
                selectinload(Project.engineering_data),
                selectinload(Project.finance_data),
            )
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, project_code: str) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(Project.project_code == project_code)
        )
        return result.scalar_one_or_none()

    async def get_projects(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Project], int]:
        query = select(Project)

        if search:
            query = query.where(
                Project.project_name.ilike(f"%{search}%")
                | Project.project_code.ilike(f"%{search}%")
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(Project.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        projects = list(result.scalars().all())

        return projects, total

    async def create_project(self, project_data: ProjectCreate, user: User) -> Project:
        project = Project(
            **project_data.model_dump(),
            created_by=user.id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_project(
        self, project: Project, project_data: ProjectUpdate, user: User
    ) -> Project:
        update_data = project_data.model_dump(exclude_unset=True)

        # Only admin and market can update most fields
        # Engineering can update status
        if user.department == Department.ENGINEERING:
            if "status" in update_data:
                project.status = update_data["status"]
        else:
            for field, value in update_data.items():
                setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()

    async def can_access_project(self, user: User, project: Project) -> bool:
        # Admin can access all
        if user.department == Department.ADMIN:
            return True
        # All departments can view all projects
        return True

    async def can_edit_project(self, user: User, project: Project) -> bool:
        # Admin can edit all
        if user.department == Department.ADMIN:
            return True
        # Market can edit project details
        if user.department == Department.MARKET:
            return True
        # Engineering can only update status
        if user.department == Department.ENGINEERING:
            return True
        return False
