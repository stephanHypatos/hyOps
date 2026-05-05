from app.database.models import Project, ProjectType, IntegrationType
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime,date

# ===================== Schemas =====================
class ProjectBase(BaseModel):
    name: str
    type: ProjectType
    start_date: date  # ISO format string (YYYY-MM-DD)
    customer_id: UUID
    deal_winner_id: UUID
    default_duration_weeks: int
    requires_integration: bool
    integration_type: IntegrationType
    partner_budget_hours: float
    internal_budget_hours: float

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ProjectType] = None
    start_date: Optional[date] = None
    customer_id: Optional[UUID] = None
    deal_winner_id: Optional[UUID] = None
    default_duration_weeks: Optional[int] = None
    requires_integration: Optional[bool] = None
    integration_type: Optional[IntegrationType] = None
    partner_budget_hours: Optional[float] = None
    internal_budget_hours: Optional[float] = None

class ProjectRead(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime




class StakeholderAssign(BaseModel):
    user_id: UUID
    role: Optional[str] = None

class StakeholderRead(BaseModel):
    project_id: UUID
    user_id: UUID
    role: Optional[str] = None
    
    

class UsecaseAssign(BaseModel):
    usecase_id: UUID