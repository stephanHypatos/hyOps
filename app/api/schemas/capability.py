from uuid import UUID
from typing import Optional
from pydantic import BaseModel



class CapabilityBase(BaseModel):
    contract: str
    name: str
    description: Optional[str] = None


class CapabilityCreate(CapabilityBase):
    pass


class CapabilityUpdate(BaseModel):
    contract: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class CapabilityRead(CapabilityBase):
    id: UUID