from fastapi import APIRouter, HTTPException
from uuid import UUID
from sqlmodel import select
from app.database.models import Usecase, FeatureUsecase, Feature, Capability
from app.database.session import SessionDep
from app.api.schemas.usecase import UsecaseCreate, UsecaseRead, UsecaseUpdate, FeatureAssign
from app.api.schemas.feature import FeatureReadWithCapability


router = APIRouter(prefix="/usecase", tags=["Usecase"])


# ===================== Usecase CRUD Endpoints =====================

@router.get("/usecases", response_model=list[UsecaseRead])
async def get_all_usecases(session: SessionDep):
    result = await session.execute(select(Usecase))
    return result.scalars().all()


@router.get("/", response_model=UsecaseRead)
async def get_usecase(id: UUID, session: SessionDep):
    usecase = await session.get(Usecase, id)
    if not usecase: 
        raise HTTPException(status_code=404, detail="Usecase not found")
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
    if not update_data: 
        raise HTTPException(status_code=400, detail="No data to update")
    usecase = await session.get(Usecase, id)
    if not usecase: 
        raise HTTPException(status_code=404, detail="Usecase not found")
    usecase.sqlmodel_update(update_data)
    session.add(usecase)
    await session.commit()
    await session.refresh(usecase)
    return usecase


@router.delete("/")
async def delete_usecase(id: UUID, session: SessionDep):
    usecase = await session.get(Usecase, id)
    if not usecase: 
        raise HTTPException(status_code=404, detail="Usecase not found")
    await session.delete(usecase)
    await session.commit()
    return {"detail": "Deleted"}


# ===================== Feature M2M Endpoints =====================

@router.get("/{usecase_id}/features", response_model=list[FeatureReadWithCapability])
async def get_usecase_features(usecase_id: UUID, session: SessionDep):
    """
    Get all features for a usecase with capability details.
    Used by: frontend feature preview + document generator adapter.
    """
    result = await session.execute(
        select(Feature, Capability)
        .join(Capability, Feature.capability_id == Capability.id)
        .join(FeatureUsecase, FeatureUsecase.feature_id == Feature.id)
        .where(FeatureUsecase.usecase_id == usecase_id)
    )
    rows = result.all()

    return [
        FeatureReadWithCapability(
            id=feature.id,
            capability_id=feature.capability_id,
            name=feature.name,
            service_description=feature.service_description,
            deliverables=feature.deliverables,
            scope_type=feature.scope_type,
            owner_id=feature.owner_id,
            scoping_questionnaire=feature.scoping_questionnaire,
            reference_documentation=feature.reference_documentation,
            included_in_ootb=feature.included_in_ootb,
            default_enabled=feature.default_enabled,
            active=feature.active,
            multiple_value=feature.multiple_value,
            requirements=feature.requirements or [],
            created_at=feature.created_at,
            updated_at=feature.updated_at,
            capability_name=capability.name,
            capability_contract=capability.contract,  # Groups features by category for docs
        )
        for feature, capability in rows
    ]


@router.post("/{usecase_id}/feature")
async def assign_feature(usecase_id: UUID, data: FeatureAssign, session: SessionDep):
    existing = await session.get(FeatureUsecase, (data.feature_id, usecase_id))
    if existing: 
        raise HTTPException(status_code=400, detail="Feature already assigned to this usecase")
    link = FeatureUsecase(usecase_id=usecase_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{usecase_id}/feature/{feature_id}")
async def remove_feature(usecase_id: UUID, feature_id: UUID, session: SessionDep):
    link = await session.get(FeatureUsecase, (feature_id, usecase_id))
    if not link: 
        raise HTTPException(status_code=404, detail="Feature not linked to this usecase")
    await session.delete(link)
    await session.commit()
    return {"detail": "Feature removed from usecase"}