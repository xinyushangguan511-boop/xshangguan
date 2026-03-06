from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, Department
from app.schemas.user import UserCreate, UserUpdate, ProfileUpdate
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
            real_name=user_data.real_name,
            phone=user_data.phone,
            email=user_data.email,
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

    async def admin_exists(self) -> bool:
        """Check if any admin user exists"""
        result = await self.db.execute(
            select(func.count(User.id)).where(User.department == Department.ADMIN)
        )
        count = result.scalar()
        return count > 0

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Admin updates a user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_password(self, user_id: UUID, new_password: str) -> Optional[User]:
        """Admin resets a user's password"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_profile(self, user_id: UUID, profile_data: ProfileUpdate) -> Optional[User]:
        """User updates own profile"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """User changes own password"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True
