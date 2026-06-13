"""
Master data CRUD endpoints for project lookup tables:
  GET/POST /countries/
  PATCH/DELETE /countries/{id}

  GET/POST /master-objectives/
  PATCH/DELETE /master-objectives/{id}

  GET/POST /master-success-criteria/
  PATCH/DELETE /master-success-criteria/{id}

  GET/POST /master-project-risks/
  PATCH/DELETE /master-project-risks/{id}

  GET/POST /master-erp-systems/
  PATCH/DELETE /master-erp-systems/{id}
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from typing import Optional

from app.database.models import (
    Country,
    MasterObjective,
    MasterSuccessCriterion,
    MasterProjectRisk,
    MasterERPSystem,
)
from app.database.session import SessionDep

router = APIRouter(tags=["Master Data"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CountryCreate(BaseModel):
    name: str
    alpha2_code: str

class CountryUpdate(BaseModel):
    name: Optional[str] = None
    alpha2_code: Optional[str] = None

class CountryRead(BaseModel):
    id: UUID
    name: str
    alpha2_code: str
    class Config: from_attributes = True


class TextItemCreate(BaseModel):
    text: str

class TextItemUpdate(BaseModel):
    text: Optional[str] = None

class TextItemRead(BaseModel):
    id: UUID
    text: str
    class Config: from_attributes = True


class ERPSystemCreate(BaseModel):
    name: str

class ERPSystemUpdate(BaseModel):
    name: Optional[str] = None

class ERPSystemRead(BaseModel):
    id: UUID
    name: str
    class Config: from_attributes = True


# ── Countries ─────────────────────────────────────────────────────────────────

@router.get("/countries/", response_model=list[CountryRead])
async def list_countries(session: SessionDep):
    result = await session.execute(select(Country).order_by(Country.name))
    return result.scalars().all()


@router.post("/countries/", response_model=CountryRead)
async def create_country(data: CountryCreate, session: SessionDep):
    code = data.alpha2_code.upper().strip()
    if len(code) != 2:
        raise HTTPException(status_code=422, detail="alpha2_code must be exactly 2 letters")
    obj = Country(name=data.name.strip(), alpha2_code=code)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/countries/{item_id}", response_model=CountryRead)
async def update_country(item_id: UUID, data: CountryUpdate, session: SessionDep):
    obj = await session.get(Country, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Country not found")
    update = data.model_dump(exclude_none=True)
    if "alpha2_code" in update:
        update["alpha2_code"] = update["alpha2_code"].upper().strip()
    obj.sqlmodel_update(update)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/countries/{item_id}")
async def delete_country(item_id: UUID, session: SessionDep):
    obj = await session.get(Country, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Country not found")
    await session.delete(obj)
    await session.commit()
    return {"detail": "Deleted"}


# ── Master Objectives ─────────────────────────────────────────────────────────

@router.get("/master-objectives/", response_model=list[TextItemRead])
async def list_objectives(session: SessionDep):
    result = await session.execute(select(MasterObjective).order_by(MasterObjective.text))
    return result.scalars().all()


@router.post("/master-objectives/", response_model=TextItemRead)
async def create_objective(data: TextItemCreate, session: SessionDep):
    obj = MasterObjective(text=data.text.strip())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/master-objectives/{item_id}", response_model=TextItemRead)
async def update_objective(item_id: UUID, data: TextItemUpdate, session: SessionDep):
    obj = await session.get(MasterObjective, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    if data.text:
        obj.text = data.text.strip()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/master-objectives/{item_id}")
async def delete_objective(item_id: UUID, session: SessionDep):
    obj = await session.get(MasterObjective, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(obj)
    await session.commit()
    return {"detail": "Deleted"}


# ── Master Success Criteria ───────────────────────────────────────────────────

@router.get("/master-success-criteria/", response_model=list[TextItemRead])
async def list_success_criteria(session: SessionDep):
    result = await session.execute(select(MasterSuccessCriterion).order_by(MasterSuccessCriterion.text))
    return result.scalars().all()


@router.post("/master-success-criteria/", response_model=TextItemRead)
async def create_success_criterion(data: TextItemCreate, session: SessionDep):
    obj = MasterSuccessCriterion(text=data.text.strip())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/master-success-criteria/{item_id}", response_model=TextItemRead)
async def update_success_criterion(item_id: UUID, data: TextItemUpdate, session: SessionDep):
    obj = await session.get(MasterSuccessCriterion, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    if data.text:
        obj.text = data.text.strip()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/master-success-criteria/{item_id}")
async def delete_success_criterion(item_id: UUID, session: SessionDep):
    obj = await session.get(MasterSuccessCriterion, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(obj)
    await session.commit()
    return {"detail": "Deleted"}


# ── Master Project Risks ──────────────────────────────────────────────────────

@router.get("/master-project-risks/", response_model=list[TextItemRead])
async def list_project_risks(session: SessionDep):
    result = await session.execute(select(MasterProjectRisk).order_by(MasterProjectRisk.text))
    return result.scalars().all()


@router.post("/master-project-risks/", response_model=TextItemRead)
async def create_project_risk(data: TextItemCreate, session: SessionDep):
    obj = MasterProjectRisk(text=data.text.strip())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/master-project-risks/{item_id}", response_model=TextItemRead)
async def update_project_risk(item_id: UUID, data: TextItemUpdate, session: SessionDep):
    obj = await session.get(MasterProjectRisk, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    if data.text:
        obj.text = data.text.strip()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/master-project-risks/{item_id}")
async def delete_project_risk(item_id: UUID, session: SessionDep):
    obj = await session.get(MasterProjectRisk, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(obj)
    await session.commit()
    return {"detail": "Deleted"}


# ── Master ERP Systems ────────────────────────────────────────────────────────

@router.get("/master-erp-systems/", response_model=list[ERPSystemRead])
async def list_erp_systems(session: SessionDep):
    result = await session.execute(select(MasterERPSystem).order_by(MasterERPSystem.name))
    return result.scalars().all()


@router.post("/master-erp-systems/", response_model=ERPSystemRead)
async def create_erp_system(data: ERPSystemCreate, session: SessionDep):
    obj = MasterERPSystem(name=data.name.strip())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/master-erp-systems/{item_id}", response_model=ERPSystemRead)
async def update_erp_system(item_id: UUID, data: ERPSystemUpdate, session: SessionDep):
    obj = await session.get(MasterERPSystem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    if data.name:
        obj.name = data.name.strip()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/master-erp-systems/{item_id}")
async def delete_erp_system(item_id: UUID, session: SessionDep):
    obj = await session.get(MasterERPSystem, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(obj)
    await session.commit()
    return {"detail": "Deleted"}
