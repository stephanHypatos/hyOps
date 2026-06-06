


from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from uuid import UUID
from sqlmodel import select
from app.database.models import Organization, OrganizationMetabaseGroup, User, UserMetabaseGroup
from app.database.session import SessionDep
from app.api.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.config import integration_settings
from app.adapters import metabase as mb_adapter



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
async def submit_organization(organization: OrganizationCreate, session: SessionDep) -> dict:
    # 1. Save the organization to the DB
    new_organization = Organization(**organization.model_dump())
    session.add(new_organization)
    await session.commit()
    await session.refresh(new_organization)

    # 2. If Metabase is configured, auto-create the permission group
    metabase_result = None
    if integration_settings.METABASE_URL and integration_settings.METABASE_API_KEY:
        group_name = new_organization.name.strip()
        try:
            mb_group = await mb_adapter.create_group(group_name)

            # 3. Write the new group ID back to the DB
            org_mb_group = OrganizationMetabaseGroup(
                organization_id=new_organization.id,
                external_id=str(mb_group["id"]),
                name=mb_group["name"],
            )
            session.add(org_mb_group)
            await session.commit()
            await session.refresh(org_mb_group)

            # 4. Auto-provision any existing users in this org into the new group
            users_result = await session.execute(
                select(User).where(User.organization_id == new_organization.id)
            )
            existing_users = users_result.scalars().all()
            provisioned = []
            for user in existing_users:
                try:
                    result = await mb_adapter.provision_user(
                        email=user.email,
                        firstname=user.first_name,
                        lastname=user.last_name,
                        group_id=mb_group["id"],
                    )
                    user.metabase_user_id = result["metabase_user_id"]
                    session.add(user)
                    session.add(UserMetabaseGroup(
                        user_id=user.id,
                        metabase_group_id=org_mb_group.id,
                    ))
                    provisioned.append(user.email)
                except Exception:
                    pass  # Don't block org creation if a user provisioning fails

            if provisioned:
                await session.commit()

            metabase_result = {
                "group_id": mb_group["id"],
                "group_name": mb_group["name"],
                "users_provisioned": provisioned,
            }

        except RuntimeError as e:
            error_str = str(e)
            if error_str.startswith("DUPLICATE_GROUP:"):
                # Parse: DUPLICATE_GROUP:<id>:<name>
                parts = error_str.split(":", 2)
                existing_id = parts[1] if len(parts) > 1 else "?"
                existing_name = parts[2] if len(parts) > 2 else group_name

                # Roll back the org we just saved and reject the request
                await session.delete(new_organization)
                await session.commit()

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "METABASE_GROUP_EXISTS",
                        "message": f"A Metabase group named '{existing_name}' already exists "
                                   f"(ID: {existing_id}). Choose a different organization name "
                                   f"or link this org to the existing group manually.",
                        "existing_group_id": existing_id,
                        "existing_group_name": existing_name,
                    }
                )
            # Any other Metabase error: org is saved but Metabase setup failed — log and continue
            metabase_result = {"error": error_str}

    return {
        "id": new_organization.id,
        "metabase": metabase_result,
    }


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