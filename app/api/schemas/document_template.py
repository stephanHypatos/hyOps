from pydantic import BaseModel
from app.database.models import  DocumentTemplateType
from uuid import UUID
from typing import Optional
from datetime import datetime

# ===================== Schemas =====================
class DocumentTemplateBase(BaseModel):
    name: str
    type: DocumentTemplateType
    markdown_content: str
    variables: list[str]  # Explicitly enforce list of strings for JSONB
    version: int
    is_active: bool
    created_by_id: UUID

class DocumentTemplateCreate(DocumentTemplateBase):
    pass

class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DocumentTemplateType] = None
    markdown_content: Optional[str] = None
    variables: Optional[list[str]] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    created_by_id: Optional[UUID] = None

class DocumentTemplateRead(DocumentTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime