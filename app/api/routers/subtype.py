from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from sqlmodel import select

from app.database.models import Subtype
from app.database.session import SessionDep

from app.api.schemas.subtype import SubtypeCreate, SubtypeRead, SubtypeUpdate


router = APIRouter(prefix="/subtype", tags=["Subtype"])


### Read all subtypes
@router.get("/subtypes", response_model=list[SubtypeRead])
async def get_all_subtypes(session: SessionDep):
    result = await session.execute(select(Subtype))
    subtypes = result.scalars().all()
    return subtypes


### Read a subtype by id
@router.get("/", response_model=SubtypeRead)
async def get_subtype(id: UUID, session: SessionDep):
    subtype = await session.get(Subtype, id)
    
    if subtype is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
    
    return subtype


@router.post("/", response_model=None)
async def submit_subtype(subtype: SubtypeCreate, session: SessionDep) -> dict[str, UUID]:
    new_subtype = Subtype(
        **subtype.model_dump()
    )
    session.add(new_subtype)
    await session.commit()
    await session.refresh(new_subtype)
    
    return {"id": new_subtype.id}


@router.patch("/", response_model=SubtypeRead)
async def update_subtype(id: UUID, subtype_update: SubtypeUpdate, session: SessionDep):
    # Get update data, ignoring fields that weren't provided
    update_data = subtype_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update"
        )
        
    subtype = await session.get(Subtype, id)
    
    # 404 check to prevent NoneType error on .sqlmodel_update()
    if subtype is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    subtype.sqlmodel_update(update_data)
    
    session.add(subtype)
    await session.commit()
    await session.refresh(subtype)
    return subtype


@router.delete("/")
async def delete_subtype(id: UUID, session: SessionDep) -> dict[str, str]:
    # Remove from database
    subtype = await session.get(Subtype, id)
    if subtype is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    await session.delete(subtype)
    await session.commit()
    
    return {"detail": f"Subtype with id #{id} is deleted!"}