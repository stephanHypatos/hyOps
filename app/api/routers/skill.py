from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from sqlmodel import  select
from app.database.models import Skill
from app.database.session import SessionDep
from app.api.schemas.skill import SkillCreate,SkillRead,SkillUpdate

router = APIRouter(prefix="/skill", tags=["Skill"])


# ===================== Endpoints =====================
@router.get("/skills", response_model=list[SkillRead])
async def get_all_skills(session: SessionDep):
    result = await session.execute(select(Skill))
    return result.scalars().all()

@router.get("/", response_model=SkillRead)
async def get_skill(id: UUID, session: SessionDep):
    skill = await session.get(Skill, id)
    if not skill: raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@router.post("/", response_model=None)
async def create_skill(data: SkillCreate, session: SessionDep) -> dict[str, UUID]:
    new_skill = Skill(**data.model_dump())
    session.add(new_skill)
    await session.commit()
    await session.refresh(new_skill)
    return {"id": new_skill.id}

@router.patch("/", response_model=SkillRead)
async def update_skill(id: UUID, data: SkillUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: raise HTTPException(status_code=400, detail="No data to update")
    skill = await session.get(Skill, id)
    if not skill: raise HTTPException(status_code=404, detail="Skill not found")
    skill.sqlmodel_update(update_data)
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill

@router.delete("/")
async def delete_skill(id: UUID, session: SessionDep):
    skill = await session.get(Skill, id)
    if not skill: raise HTTPException(status_code=404, detail="Skill not found")
    await session.delete(skill)
    await session.commit()
    return {"detail": "Deleted"}