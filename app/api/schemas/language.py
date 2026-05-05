
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


# ===================== Schemas =====================
class LanguageBase(BaseModel):
    code: str
    name: str

class LanguageCreate(LanguageBase):
    pass

class LanguageUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class LanguageRead(LanguageBase):
    id: UUID