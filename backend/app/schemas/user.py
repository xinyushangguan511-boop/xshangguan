from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from app.models.user import Department


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    department: Department
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    department: Department
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """For admin to update user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    department: Optional[Department] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserResetPassword(BaseModel):
    """For admin to reset user password"""
    new_password: str = Field(..., min_length=6)


class ProfileUpdate(BaseModel):
    """For user to update own profile"""
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class PasswordChange(BaseModel):
    """For user to change own password"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    department: str
    exp: int


class RegistrationStatus(BaseModel):
    """Check if registration is allowed"""
    registration_allowed: bool
    message: str
