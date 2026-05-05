from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import Optional
from sqlmodel import SQLModel, select
from app.database.models import Usecase, FeatureUsecase
from app.database.session import SessionDep
from app.api.schemas.usecase import UsecaseCreate,UsecaseRead,UsecaseUpdate,FeatureAssign


router = APIRouter(prefix="/usecase", tags=["Usecase"])



# ===================== Usecase CRUD Endpoints =====================
@router.get("/usecases", response_model=list[UsecaseRead])
async def get_all_usecases(session: SessionDep):
    result = await session.execute(select(Usecase))
    return result.scalars().all()

@router.get("/", response_model=UsecaseRead)
async def get_usecase(id: UUID, session: SessionDep):
    usecase = await session.get(Usecase, id)
    if not usecase: raise HTTPException(status_code=404, detail="Usecase not found")
    return usecase

@router.post("/", response_model=None)
async def create_usecase(data: UsecaseCreate, session: SessionDep) -> dict[str, UUID]:
    new_usecase = Usecase(**data.model_dump())
    session.add(new_usecase)
    await session.commit()
    await session.refresh(new_usecase)
    return {"id": new_usecase.id}

@router.patch("/", response_model=UsecaseRead)
async def update_usecase(id: UUID, data: UsecaseUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: raise HTTPException(status_code=400, detail="No data to update")
    usecase = await session.get(Usecase, id)
    if not usecase: raise HTTPException(status_code=404, detail="Usecase not found")
    usecase.sqlmodel_update(update_data)
    session.add(usecase)
    await session.commit()
    await session.refresh(usecase)
    return usecase

@router.delete("/")
async def delete_usecase(id: UUID, session: SessionDep):
    usecase = await session.get(Usecase, id)
    if not usecase: raise HTTPException(status_code=404, detail="Usecase not found")
    await session.delete(usecase)
    await session.commit()
    return {"detail": "Deleted"}

# ===================== Feature M2M Endpoints =====================
@router.get("/{usecase_id}/features")
async def get_usecase_features(usecase_id: UUID, session: SessionDep):
    result = await session.execute(
        select(FeatureUsecase).where(FeatureUsecase.usecase_id == usecase_id)
    )
    return result.scalars().all()

@router.post("/{usecase_id}/feature")
async def assign_feature(usecase_id: UUID, data: FeatureAssign, session: SessionDep):
    existing = await session.get(FeatureUsecase, (data.feature_id, usecase_id))
    if existing: raise HTTPException(status_code=400, detail="Feature already assigned to this usecase")
    link = FeatureUsecase(usecase_id=usecase_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link

@router.delete("/{usecase_id}/feature/{feature_id}")
async def remove_feature(usecase_id: UUID, feature_id: UUID, session: SessionDep):
    link = await session.get(FeatureUsecase, (feature_id, usecase_id))
    if not link: raise HTTPException(status_code=404, detail="Feature not linked to this usecase")
    await session.delete(link)
    await session.commit()
    return {"detail": "Feature removed from usecase"}