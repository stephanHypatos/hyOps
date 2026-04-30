

from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.database.models import ScopeType





# ===================== Schemas =====================

class FeatureBase(BaseModel):
    capability_id: UUID
    name: str
    service_description: str
    requirement_description: str
    solution_description: str
    deliverables: str
    scope_type: ScopeType
    owner_id: UUID
    scoping_questionnaire: bool
    reference_documentation: Optional[str] = None
    included_in_ootb: bool
    default_enabled: bool
    active: bool
    multiple_value: int


class FeatureCreate(FeatureBase):
    pass


class FeatureUpdate(BaseModel):
    capability_id: Optional[UUID] = None
    name: Optional[str] = None
    service_description: Optional[str] = None
    requirement_description: Optional[str] = None
    solution_description: Optional[str] = None
    deliverables: Optional[str] = None
    scope_type: Optional[ScopeType] = None
    owner_id: Optional[UUID] = None
    scoping_questionnaire: Optional[bool] = None
    reference_documentation: Optional[str] = None
    included_in_ootb: Optional[bool] = None
    default_enabled: Optional[bool] = None
    active: Optional[bool] = None
    multiple_value: Optional[int] = None


class FeatureRead(FeatureBase):
    id: UUID
    created_at: datetime
    updated_at: datetime