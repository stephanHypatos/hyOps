from typing import Optional
from pydantic import EmailStr, BaseModel
from sqlmodel import SQLModel, select
from uuid import UUID
from app.database.models import UserType, UserRole
from datetime import datetime

class UserBase(BaseModel):
    organization_id: UUID
    type: UserType
    subtype_id: UUID
    role: UserRole
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    organization_id: Optional[UUID] = None
    type: Optional[UserType] = None
    subtype_id: Optional[UUID] = None
    role: Optional[UserRole] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
