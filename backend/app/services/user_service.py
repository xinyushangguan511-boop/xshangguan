from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            department=user_data.department,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.get_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_all_users(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())
