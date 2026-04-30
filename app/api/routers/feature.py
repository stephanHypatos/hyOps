from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from datetime import datetime
from sqlmodel import select

from app.database.models import Feature
from app.database.session import SessionDep
from app.api.schemas.feature import FeatureRead, FeatureCreate, FeatureUpdate



# ===================== Router =====================

router = APIRouter(prefix="/feature", tags=["Feature"])


### Read all features
@router.get("/features", response_model=list[FeatureRead])
async def get_all_features(session: SessionDep):
    result = await session.execute(select(Feature))
    features = result.scalars().all()
    return features


### Read a feature by id
@router.get("/", response_model=FeatureRead)
async def get_feature(id: UUID, session: SessionDep):
    feature = await session.get(Feature, id)
    
    if feature is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
    
    return feature


@router.post("/", response_model=None)
async def submit_feature(feature: FeatureCreate, session: SessionDep) -> dict[str, UUID]:
    new_feature = Feature(
        **feature.model_dump()
    )
    session.add(new_feature)
    await session.commit()
    await session.refresh(new_feature)
    
    return {"id": new_feature.id}


@router.patch("/", response_model=FeatureRead)
async def update_feature(id: UUID, feature_update: FeatureUpdate, session: SessionDep):
    # Get update data, ignoring fields that weren't provided
    update_data = feature_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update"
        )
        
    feature = await session.get(Feature, id)
    
    # 404 check to prevent NoneType error on .sqlmodel_update()
    if feature is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    # Update the timestamp manually since we are modifying the record
    update_data["updated_at"] = datetime.now()
    
    feature.sqlmodel_update(update_data)
    
    session.add(feature)
    await session.commit()
    await session.refresh(feature)
    return feature


@router.delete("/")
async def delete_feature(id: UUID, session: SessionDep) -> dict[str, str]:
    # Remove from database
    feature = await session.get(Feature, id)
    if feature is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    await session.delete(feature)
    await session.commit()
    
    return {"detail": f"Feature with id #{id} is deleted!"}