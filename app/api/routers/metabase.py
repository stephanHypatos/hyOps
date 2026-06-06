"""
Metabase integration endpoints.

Org-level:   PUT  /metabase/organization/{org_id}/group
             GET  /metabase/groups

User-level:  POST   /metabase/user/{user_id}/provision
             GET    /metabase/user/{user_id}/memberships
             DELETE /metabase/user/{user_id}/group/{group_id}
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.adapters import metabase as mb_adapter
from app.database.models import (
    Organization,
    OrganizationMetabaseGroup,
    User,
    UserMetabaseGroup,
)
from app.database.session import SessionDep

router = APIRouter(prefix="/metabase", tags=["Metabase Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class MetabaseGroupAssign(BaseModel):
    external_id: str   # Metabase's integer group ID (stored as string)
    name: str


class MetabaseProvisionResponse(BaseModel):
    email: str
    metabase_user_id: int
    metabase_group_id: int
    user_exists: bool
    created: bool


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/groups")
async def list_metabase_groups():
    """List all non-system Metabase permission groups (for use in dropdowns)."""
    try:
        return await mb_adapter.list_groups()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Metabase error: {str(e)}")


@router.put("/organization/{org_id}/group")
async def assign_metabase_group_to_org(
    org_id: UUID,
    body: MetabaseGroupAssign,
    session: SessionDep,
):
    """
    Assign (or update) a Metabase permission group for an organization.
    Creates the OrganizationMetabaseGroup record if it doesn't exist yet.
    """
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    result = await session.execute(
        select(OrganizationMetabaseGroup).where(
            OrganizationMetabaseGroup.organization_id == org_id
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.external_id = body.external_id
        existing.name = body.name
        session.add(existing)
    else:
        new_group = OrganizationMetabaseGroup(
            organization_id=org_id,
            external_id=body.external_id,
            name=body.name,
        )
        session.add(new_group)

    await session.commit()
    return {"detail": f"Metabase group '{body.name}' assigned to organization"}


# ── User-level ────────────────────────────────────────────────────────────────

@router.post("/user/{user_id}/provision", response_model=MetabaseProvisionResponse)
async def provision_user_in_metabase(user_id: UUID, session: SessionDep):
    """
    Provision the user in Metabase and add them to their organization's Metabase group.
    - If the user already exists in Metabase, they are just added to the group (idempotent).
    - Stores the Metabase user ID on the User record for future lookups.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Look up the org's Metabase group
    result = await session.execute(
        select(OrganizationMetabaseGroup).where(
            OrganizationMetabaseGroup.organization_id == user.organization_id
        )
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No Metabase group configured for this user's organization. "
                   "Set one via PUT /metabase/organization/{org_id}/group first.",
        )

    try:
        group_id = int(org_group.external_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid Metabase group ID '{org_group.external_id}' — must be an integer",
        )

    try:
        result_data = await mb_adapter.provision_user(
            email=user.email,
            firstname=user.first_name,
            lastname=user.last_name,
            group_id=group_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Metabase error: {str(e)}")

    # Persist the Metabase user ID on the user record
    user.metabase_user_id = result_data["metabase_user_id"]
    user.updated_at = datetime.utcnow()
    session.add(user)

    # Create UserMetabaseGroup link if not already present
    link_result = await session.execute(
        select(UserMetabaseGroup).where(
            UserMetabaseGroup.user_id == user_id,
            UserMetabaseGroup.metabase_group_id == org_group.id,
        )
    )
    if link_result.scalars().first() is None:
        session.add(UserMetabaseGroup(user_id=user_id, metabase_group_id=org_group.id))

    await session.commit()
    return MetabaseProvisionResponse(**result_data)


@router.get("/user/{user_id}/memberships")
async def get_user_metabase_memberships(user_id: UUID, session: SessionDep):
    """Get the user's current Metabase permission group memberships (live from Metabase API)."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.metabase_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not been provisioned in Metabase yet",
        )
    try:
        memberships = await mb_adapter.get_user_memberships(user.metabase_user_id)
        return {"metabase_user_id": user.metabase_user_id, "memberships": memberships}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Metabase error: {str(e)}")


@router.delete("/user/{user_id}/group/{metabase_group_id}")
async def remove_user_from_metabase_group(
    user_id: UUID,
    metabase_group_id: int,
    session: SessionDep,
):
    """Remove the user from a specific Metabase permission group."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.metabase_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not been provisioned in Metabase yet",
        )
    try:
        removed = await mb_adapter.remove_from_group(user.metabase_user_id, metabase_group_id)
        return {"removed": removed, "detail": "User removed from group" if removed else "User was not in that group"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Metabase error: {str(e)}")
