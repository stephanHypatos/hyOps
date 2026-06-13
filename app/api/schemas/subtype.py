from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class SubtypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class SubtypeCreate(SubtypeBase):
    pass


class SubtypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubtypeRead(SubtypeBase):
    id: UUID
