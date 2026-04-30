from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from sqlmodel import  select

from app.database.models import Capability
from app.database.session import SessionDep
from app.api.schemas.capability import CapabilityRead,CapabilityCreate,CapabilityUpdate



# ===================== Router =====================

router = APIRouter(prefix="/capability", tags=["Capability"])


### Read all capabilities
@router.get("/capabilities", response_model=list[CapabilityRead])
async def get_all_capabilities(session: SessionDep):
    result = await session.execute(select(Capability))
    capabilities = result.scalars().all()
    return capabilities


### Read a capability by id
@router.get("/", response_model=CapabilityRead)
async def get_capability(id: UUID, session: SessionDep):
    capability = await session.get(Capability, id)
    
    if capability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
    
    return capability


@router.post("/", response_model=None)
async def submit_capability(capability: CapabilityCreate, session: SessionDep) -> dict[str, UUID]:
    new_capability = Capability(
        **capability.model_dump()
    )
    session.add(new_capability)
    await session.commit()
    await session.refresh(new_capability)
    
    return {"id": new_capability.id}


@router.patch("/", response_model=CapabilityRead)
async def update_capability(id: UUID, capability_update: CapabilityUpdate, session: SessionDep):
    # Get update data, ignoring fields that weren't provided
    update_data = capability_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update"
        )
        
    capability = await session.get(Capability, id)
    
    # 404 check to prevent NoneType error on .sqlmodel_update()
    if capability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    capability.sqlmodel_update(update_data)
    
    session.add(capability)
    await session.commit()
    await session.refresh(capability)
    return capability


@router.delete("/")
async def delete_capability(id: UUID, session: SessionDep) -> dict[str, str]:
    # Remove from database
    capability = await session.get(Capability, id)
    if capability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    await session.delete(capability)
    await session.commit()
    
    return {"detail": f"Capability with id #{id} is deleted!"}