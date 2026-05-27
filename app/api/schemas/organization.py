from pydantic import BaseModel, Field, EmailStr
from app.database.models import OrganizationType
from datetime import datetime
from uuid import UUID
from typing import Optional


class OrganizationBase(BaseModel):
    name: str
    type: OrganizationType
    email: EmailStr
    industry: str
    country: str
    regions_operation: Optional[str] = None
    number_subsidiaries: Optional[str] = None
    company_overview: Optional[str] = None
    languages: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[OrganizationType] = None
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    regions_operation: Optional[str] = None
    number_subsidiaries: Optional[str] = None
    company_overview: Optional[str] = None
    languages: Optional[str] = None


class OrganizationRead(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Override inherited Optional fields so response always shows them
    # (they'll be None if not set, which is valid JSON)
    regions_operation: Optional[str] = None
    number_subsidiaries: Optional[str] = None
    company_overview: Optional[str] = None
    languages: Optional[str] = None