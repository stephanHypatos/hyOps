
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

# ===================== Schemas =====================
class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None

class SkillRead(SkillBase):
    id: UUID
