from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from uuid import UUID
from sqlmodel import select

from app.database.models import User
from app.database.session import SessionDep
from app.api.schemas.user import UserCreate,UserRead,UserUpdate


router = APIRouter(prefix="/user", tags=["User"])


### Read all users
@router.get("/users", response_model=list[UserRead])
async def get_all_users(session: SessionDep):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


### Read a user by id
@router.get("/", response_model=UserRead)
async def get_user(id: UUID, session: SessionDep):
    user = await session.get(User, id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
    
    return user


@router.post("/", response_model=None)
async def submit_user(user: UserCreate, session: SessionDep) -> dict[str, UUID]:
    new_user = User(
        **user.model_dump()
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return {"id": new_user.id}


@router.patch("/", response_model=UserRead)
async def update_user(id: UUID, user_update: UserUpdate, session: SessionDep):
    # Get update data, ignoring fields that weren't provided
    update_data = user_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update"
        )
        
    user = await session.get(User, id)
    
    # Added 404 check to prevent NoneType error on .sqlmodel_update()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    # Update the timestamp manually since we are modifying the record
    update_data["updated_at"] = datetime.now()
    
    user.sqlmodel_update(update_data)
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/")
async def delete_user(id: UUID, session: SessionDep) -> dict[str, str]:
    # Remove from database
    user = await session.get(User, id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!"
        )
        
    await session.delete(user)
    await session.commit()
    
    return {"detail": f"User with id #{id} is deleted!"}