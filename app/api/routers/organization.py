# from fastapi import APIRouter

# from datetime import datetime, timedelta

# from fastapi import  HTTPException, status


# from app.database.models import Shipment, ShipmentStatus
# from app.database.session import SessionDep

# from app.api.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate


# router = APIRouter(prefix="/shipment",tags=["Shipment"])


# ### Read a shipment by id
# @router.get("/shipment", response_model=ShipmentRead)
# async def get_shipment(id:int,session: SessionDep):
#     shipment = await session.get(Shipment, id)
    
#     if shipment is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Given id doesn't exist!"
#         )
    
#     return shipment

# @router.post("/shipment", response_model=None)
# async def submit_shipment(shipment:ShipmentCreate,session: SessionDep) -> dict[str,int]:
#     new_shipment = Shipment(
#         **shipment.model_dump(),
#         status=ShipmentStatus.placed,
#         estimated_delivery=datetime.now() + timedelta(days=3)
#     )
#     session.add(new_shipment)
#     await session.commit()
#     await session.refresh(new_shipment)
    
#     return {"id": new_shipment.id}


# @router.patch("/shipment", response_model=ShipmentRead)
# async def update_shipment(id:int,shipment_update: ShipmentUpdate,session: SessionDep):
#     # update data with given fields
#     update = shipment_update.model_dump(exclude_none=True)
#     if not update:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="No data provided to update"
#         )
#     shipment = await session.get(Shipment, id)
#     shipment.sqlmodel_update(
#         update
#     )
    
#     session.add(shipment)
#     await session.commit()
#     await session.refresh(shipment)
#     return shipment


# @router.delete("/shipment")
# async def delete_shipment(id:int,session: SessionDep) -> dict[str,str]:
#     # Remove from database
#     shipment = await session.get(Shipment, id)
#     if shipment is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Given id doesn't exist!"
#         )
#     await session.delete(session.get(Shipment, id))
#     await session.commit()
    
#     return {"detail":f"Shipment with id #{id} is deleted!"}



from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from uuid import UUID
from sqlmodel import select
from app.database.models import Organization
from app.database.session import SessionDep
from app.api.schemas.organization import OrganizationCreate,OrganizationRead,OrganizationUpdate



router = APIRouter(prefix="/organization", tags=["Organization"])


### Read all organizations
@router.get("/organizations", response_model=list[OrganizationRead])
async def get_all_organizations(session: SessionDep):
    result = await session.execute(select(Organization))
    organizations = result.scalars().all()
    return organizations


### Read an organization by id
@router.get("/", response_model=OrganizationRead)
async def get_organization(id: UUID, session: SessionDep):
    organization = await session.get(Organization, id)
    
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
    
    return organization


@router.post("/", response_model=None)
async def submit_organization(organization: OrganizationCreate, session: SessionDep) -> dict[str, UUID]:
    new_organization = Organization(
        **organization.model_dump()
    )
    session.add(new_organization)
    await session.commit()
    await session.refresh(new_organization)
    
    return {"id": new_organization.id}


@router.patch("/", response_model=OrganizationRead)
async def update_organization(id: UUID, organization_update: OrganizationUpdate, session: SessionDep):
    # Get update data, ignoring fields that weren't provided
    update_data = organization_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update"
        )
        
    organization = await session.get(Organization, id)
    
    # Added 404 check to prevent NoneType error on .sqlmodel_update()
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    # Update the timestamp manually since we are modifying the record
    update_data["updated_at"] = datetime.now()
    
    organization.sqlmodel_update(update_data)
    
    session.add(organization)
    await session.commit()
    await session.refresh(organization)
    return organization


@router.delete("/")
async def delete_organization(id: UUID, session: SessionDep) -> dict[str, str]:
    # Remove from database
    organization = await session.get(Organization, id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    await session.delete(organization)
    await session.commit()
    
    return {"detail": f"Organization with id #{id} is deleted!"}