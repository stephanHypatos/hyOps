from pydantic import BaseModel
from app.database.models import  DocumentTemplateType
from uuid import UUID
from typing import Optional
from datetime import datetime

# ===================== Schemas =====================
class DocumentTemplateBase(BaseModel):
    file_format: str = "md"  # "md" or "docx"
    name: str
    type: DocumentTemplateType
    markdown_content: str
    variables: list[str]  # Explicitly enforce list of strings for JSONB
    version: float
    is_active: bool
    created_by_id: UUID

class DocumentTemplateCreate(DocumentTemplateBase):
    pass

class DocumentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DocumentTemplateType] = None
    markdown_content: Optional[str] = None
    variables: Optional[list[str]] = None
    version: Optional[float] = None
    is_active: Optional[bool] = None
    file_format: Optional[str] = None
    created_by_id: Optional[UUID] = None

class DocumentTemplateRead(DocumentTemplateBase):
    id: UUID
    # REMOVED: file_path: Optional[str] = None  <-- No longer needed since we aren't saving base template files
    created_at: datetime
    updated_at: datetime