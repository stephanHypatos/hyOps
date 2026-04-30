
from uuid import UUID
from typing import Optional

from app.database.models import SubtypeName
from pydantic import BaseModel

class SubtypeBase(BaseModel):
    name: SubtypeName
    description: Optional[str] = None


class SubtypeCreate(SubtypeBase):
    pass


class SubtypeUpdate(BaseModel):
    name: Optional[SubtypeName] = None
    description: Optional[str] = None


class SubtypeRead(SubtypeBase):
    id: UUID