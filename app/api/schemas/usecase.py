from uuid import UUID
from typing import Optional
from pydantic import BaseModel


# ===================== Schemas =====================

class UsecaseBase(BaseModel):
    name: str
    description: Optional[str] = None


class UsecaseCreate(UsecaseBase):
    pass


class UsecaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class UsecaseRead(UsecaseBase):
    id: UUID


class FeatureAssign(BaseModel):
    feature_id: UUID