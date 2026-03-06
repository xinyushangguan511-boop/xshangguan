from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, Token,
    ProfileUpdate, PasswordChange, RegistrationStatus
)
from app.services.user_service import UserService
from app.utils.security import create_access_token, create_refresh_token, decode_token
from app.utils.dependencies import get_current_active_user
from app.models.user import User, Department

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.get("/registration-status", response_model=RegistrationStatus)
async def check_registration_status(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Check if registration is allowed (only before first admin is created)"""
    service = UserService(db)
    admin_exists = await service.admin_exists()

    if admin_exists:
        return RegistrationStatus(
            registration_allowed=False,
            message="注册已关闭，请联系管理员创建账户"
        )
    return RegistrationStatus(
        registration_allowed=True,
        message="请注册管理员账户"
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)

    # Check if admin exists - if so, registration is closed
    admin_exists = await service.admin_exists()
    if admin_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="注册已关闭，请联系管理员创建账户",
        )

    # First user must be admin
    if user_data.department != Department.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="首个用户必须是管理员账户",
        )

    existing = await service.get_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    user = await service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    user = await service.authenticate(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    token_data = {
        "sub": str(user.id),
        "department": user.department.value,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    service = UserService(db)
    user = await service.get_by_id(payload.get("sub"))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {
        "sub": str(user.id),
        "department": user.department.value,
    }

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user's profile"""
    service = UserService(db)
    user = await service.update_profile(current_user.id, profile_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change current user's password"""
    service = UserService(db)
    success = await service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误",
        )

    return {"message": "密码修改成功"}
