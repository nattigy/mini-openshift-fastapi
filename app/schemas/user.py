from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.models.core import UserRole

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    role: UserRole = UserRole.DEVELOPER
    username: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[UUID] = None

    class Config:
        from_attributes = True

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

# Password change schema
class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
