from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from sqlmodel import  select
from app.database.models import Language
from app.database.session import SessionDep
from app.api.schemas.language import LanguageCreate,LanguageRead,LanguageUpdate


router = APIRouter(prefix="/language", tags=["Language"])



# ===================== Endpoints =====================
@router.get("/languages", response_model=list[LanguageRead])
async def get_all_languages(session: SessionDep):
    result = await session.execute(select(Language))
    return result.scalars().all()

@router.get("/", response_model=LanguageRead)
async def get_language(id: UUID, session: SessionDep):
    language = await session.get(Language, id)
    if not language: raise HTTPException(status_code=404, detail="Language not found")
    return language

@router.post("/", response_model=None)
async def create_language(data: LanguageCreate, session: SessionDep) -> dict[str, UUID]:
    new_lang = Language(**data.model_dump())
    session.add(new_lang)
    await session.commit()
    await session.refresh(new_lang)
    return {"id": new_lang.id}

@router.patch("/", response_model=LanguageRead)
async def update_language(id: UUID, data: LanguageUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: raise HTTPException(status_code=400, detail="No data to update")
    language = await session.get(Language, id)
    if not language: raise HTTPException(status_code=404, detail="Language not found")
    language.sqlmodel_update(update_data)
    session.add(language)
    await session.commit()
    await session.refresh(language)
    return language

@router.delete("/")
async def delete_language(id: UUID, session: SessionDep):
    language = await session.get(Language, id)
    if not language: raise HTTPException(status_code=404, detail="Language not found")
    await session.delete(language)
    await session.commit()
    return {"detail": "Deleted"}