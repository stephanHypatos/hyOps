from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class DocumentationLinkBase(BaseModel):
    title: str
    url: str
    description: Optional[str] = None


class DocumentationLinkCreate(DocumentationLinkBase):
    pass


class DocumentationLinkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class DocumentationLinkRead(DocumentationLinkBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
