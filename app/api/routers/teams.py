"""
Microsoft Teams integration endpoints.

Org-level:   PUT  /teams/organization/{org_id}/group
User-level:  POST /teams/user/{user_id}/add
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.adapters import teams as teams_adapter
from app.database.models import (
    Organization,
    OrganizationTeamsGroup,
    User,
    UserTeamsGroup,
)
from app.database.session import SessionDep

router = APIRouter(prefix="/teams", tags=["Teams Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TeamsGroupAssign(BaseModel):
    external_id: str  # Microsoft 365 Group / Team ID
    name: str


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/organization/{org_id}/group")
async def get_teams_group_for_org(org_id: UUID, session: SessionDep):
    """Get the Teams group configured for an organization."""
    result = await session.execute(
        select(OrganizationTeamsGroup).where(
            OrganizationTeamsGroup.organization_id == org_id
        )
    )
    group = result.scalars().first()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Teams group configured for this organization")
    return {"external_id": group.external_id, "name": group.name, "id": str(group.id)}


@router.put("/organization/{org_id}/group")
async def assign_teams_group_to_org(
    org_id: UUID,
    body: TeamsGroupAssign,
    session: SessionDep,
):
    """Assign (or update) a Teams group/channel for an organization."""
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    result = await session.execute(
        select(OrganizationTeamsGroup).where(
            OrganizationTeamsGroup.organization_id == org_id
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.external_id = body.external_id
        existing.name = body.name
        session.add(existing)
    else:
        session.add(OrganizationTeamsGroup(
            organization_id=org_id,
            external_id=body.external_id,
            name=body.name,
        ))

    await session.commit()
    return {"detail": f"Teams group '{body.name}' assigned to organization"}


# ── User-level ────────────────────────────────────────────────────────────────

@router.post("/user/{user_id}/add")
async def add_user_to_teams(user_id: UUID, session: SessionDep):
    """
    Invite the user to Azure AD (if not already there) and add them to the
    organization's configured Teams group.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await session.execute(
        select(OrganizationTeamsGroup).where(
            OrganizationTeamsGroup.organization_id == user.organization_id
        )
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No Teams group configured for this user's organization. "
                   "Set one via PUT /teams/organization/{org_id}/group first.",
        )

    display_name = f"{user.first_name} {user.last_name}".strip()

    try:
        data = await teams_adapter.add_user_to_teams(
            email=user.email,
            display_name=display_name,
            team_id=org_group.external_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {str(e)}")

    # Create UserTeamsGroup link if not already present
    link_result = await session.execute(
        select(UserTeamsGroup).where(
            UserTeamsGroup.user_id == user_id,
            UserTeamsGroup.teams_group_id == org_group.id,
        )
    )
    if link_result.scalars().first() is None:
        session.add(UserTeamsGroup(user_id=user_id, teams_group_id=org_group.id))
        await session.commit()

    return {
        "detail": "User added to Teams group",
        "teams_group": org_group.name,
        **data,
    }
