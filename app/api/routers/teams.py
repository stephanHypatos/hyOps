"""
Microsoft Teams integration endpoints.

Org-level:
    GET    /teams/teams                               — list all Teams in tenant
    GET    /teams/organization/{org_id}/group         — get linked team for org
    POST   /teams/organization/{org_id}/create-team   — check dup + create + store
    PUT    /teams/organization/{org_id}/group         — link existing team by ID
    DELETE /teams/organization/{org_id}/group         — unlink team from org (DB only)
    GET    /teams/organization/{org_id}/members       — live team members from Graph
    DELETE /teams/organization/{org_id}/members/{mid} — remove a member from the team

User-level:
    POST   /teams/user/{user_id}/add                  — get-or-invite + add to team
    GET    /teams/user/{user_id}/membership           — live membership status for this user
    DELETE /teams/user/{user_id}/remove               — remove user from their org's team

Admin:
    GET    /teams/users                               — list all Azure AD users
    DELETE /teams/users/{user_object_id}              — permanently delete Azure AD user
"""

import logging
from datetime import datetime
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["Teams Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TeamsGroupAssign(BaseModel):
    external_id: str  # Microsoft 365 Group / Team ID
    name: str


# ── Admin: list all Teams ──────────────────────────────────────────────────────

@router.get("/teams")
async def list_all_teams():
    """List all Teams teams in the tenant (live from Microsoft Graph)."""
    try:
        return await teams_adapter.list_teams()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams list_teams error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


@router.delete("/teams/{team_id}")
async def delete_teams_team(team_id: str):
    """
    Permanently delete a Microsoft Teams team (admin operation).
    Deletes the underlying M365 group — use with caution.
    """
    try:
        await teams_adapter.delete_team(team_id)
        return {"detail": f"Teams team {team_id} deleted"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Teams delete_team error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/organization/{org_id}/group")
async def get_teams_group_for_org(org_id: UUID, session: SessionDep):
    """Get the Teams group/team configured for an organization."""
    result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
    )
    group = result.scalars().first()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Teams group configured for this organization",
        )
    return {"external_id": group.external_id, "name": group.name, "id": str(group.id)}


@router.post("/organization/{org_id}/create-team")
async def create_teams_team_for_org(org_id: UUID, session: SessionDep):
    """
    Manually create a new Microsoft Teams team for this organization.
    - Uses the organization name as the team displayName.
    - Checks for a duplicate team first (returns 409 if one exists).
    - Creates the team (async — may take up to ~60s for MS to provision).
    - Admin user (TEAMS_ADMIN_USER_ID) is added as owner automatically.
    - Stores the resulting team ID in OrganizationTeamsGroup.
    - Provisions all existing org users into the new team.
    """
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    team_name = org.name.strip()
    logger.info("Teams: create-team requested for org '%s' (%s)", team_name, org_id)

    try:
        result_data = await teams_adapter.create_team_for_org(team_name)
    except RuntimeError as e:
        logger.error("Teams create_team_for_org failed: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error("Teams create_team_for_org unexpected error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{type(e).__name__}: {e}",
        )

    if result_data.get("already_exists"):
        # Return 409 — team already exists in MS, let user link it manually
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "TEAMS_TEAM_EXISTS",
                "message": f"A Teams team named '{team_name}' already exists (ID: {result_data['id']}). "
                           f"Use 'Link existing team' to connect it.",
                "existing_team_id": result_data["id"],
                "existing_team_name": result_data["name"],
            },
        )

    # Upsert OrganizationTeamsGroup
    link_result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
    )
    org_group = link_result.scalars().first()
    if org_group:
        org_group.external_id = result_data["id"]
        org_group.name = result_data["name"]
    else:
        org_group = OrganizationTeamsGroup(
            organization_id=org_id,
            external_id=result_data["id"],
            name=result_data["name"],
        )
    session.add(org_group)
    await session.commit()
    await session.refresh(org_group)

    # Provision existing org users into the new team
    users_result = await session.execute(select(User).where(User.organization_id == org_id))
    existing_users = users_result.scalars().all()
    provisioned = []
    failed = []
    for user in existing_users:
        try:
            display_name = f"{user.first_name} {user.last_name}".strip()
            prov = await teams_adapter.provision_user_to_team(
                email=user.email,
                display_name=display_name,
                team_id=result_data["id"],
            )
            user.teams_user_id = prov["teams_user_object_id"]
            user.updated_at = datetime.utcnow()
            session.add(user)

            # Create UserTeamsGroup link if not already present
            ug_check = await session.execute(
                select(UserTeamsGroup).where(
                    UserTeamsGroup.user_id == user.id,
                    UserTeamsGroup.teams_group_id == org_group.id,
                )
            )
            if ug_check.scalars().first() is None:
                session.add(UserTeamsGroup(user_id=user.id, teams_group_id=org_group.id))

            provisioned.append(user.email)
        except Exception as ex:
            logger.warning("Teams: failed to provision user %s: %s", user.email, ex)
            failed.append({"email": user.email, "error": str(ex)})

    if provisioned:
        await session.commit()

    return {
        "teams_team_id": result_data["id"],
        "teams_team_name": result_data["name"],
        "created": result_data["created"],
        "users_provisioned": provisioned,
        "users_failed": failed,
    }


@router.put("/organization/{org_id}/group")
async def assign_teams_group_to_org(org_id: UUID, body: TeamsGroupAssign, session: SessionDep):
    """Manually link (or re-link) an existing Teams team to an organization."""
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
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
    return {"detail": f"Teams team '{body.name}' linked to organization"}


@router.delete("/organization/{org_id}/group")
async def unlink_teams_group_from_org(org_id: UUID, session: SessionDep):
    """
    Unlink the Teams team from an organization (DB only — does NOT delete the team in MS Teams).
    Also removes UserTeamsGroup links for users in this org.
    """
    result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Teams group linked to this organization",
        )

    # Remove all UserTeamsGroup links for this group
    user_links = await session.execute(
        select(UserTeamsGroup).where(UserTeamsGroup.teams_group_id == org_group.id)
    )
    for link in user_links.scalars().all():
        await session.delete(link)

    await session.delete(org_group)
    await session.commit()
    return {"detail": "Teams team unlinked from organization"}


@router.get("/organization/{org_id}/members")
async def get_team_members_for_org(org_id: UUID, session: SessionDep):
    """Get live team members from Microsoft Graph for the organization's linked Teams team."""
    result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Teams group configured for this organization",
        )
    try:
        members = await teams_adapter.get_team_members(org_group.external_id)
        return {
            "team_id": org_group.external_id,
            "team_name": org_group.name,
            "members": members,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams get_team_members error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


@router.delete("/organization/{org_id}/members/{membership_id}")
async def remove_team_member_for_org(org_id: UUID, membership_id: str, session: SessionDep):
    """Remove a member from the organization's Teams team by their Teams membership ID."""
    result = await session.execute(
        select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id)
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Teams group configured for this organization",
        )
    try:
        removed = await teams_adapter.remove_member_from_team(org_group.external_id, membership_id)
        return {
            "removed": removed,
            "detail": "Member removed from Teams team" if removed else "Member was not in that team",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams remove_member error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


# ── User-level ────────────────────────────────────────────────────────────────

@router.post("/user/{user_id}/add")
async def add_user_to_teams_team(user_id: UUID, session: SessionDep):
    """
    Provision a user to their organization's Microsoft Teams team.
    - Looks up or invites the user in Azure AD.
    - Adds them to the linked team.
    - Stores the Azure AD object ID on the User record.
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
                   "Create or link a team via the Integrations page first.",
        )

    display_name = f"{user.first_name} {user.last_name}".strip()

    try:
        data = await teams_adapter.provision_user_to_team(
            email=user.email,
            display_name=display_name,
            team_id=org_group.external_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams provision_user_to_team error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")

    # Persist Azure AD object ID on user record
    user.teams_user_id = data["teams_user_object_id"]
    user.updated_at = datetime.utcnow()
    session.add(user)

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
        "detail": "User added to Teams team",
        "teams_group": org_group.name,
        "teams_guest_invited": data["teams_guest_invited"],
        **data,
    }


@router.get("/user/{user_id}/membership")
async def get_user_teams_membership(user_id: UUID, session: SessionDep):
    """
    Get live Teams membership status for this user.
    Returns org team info + whether user is currently in the team + their membership_id.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Get org's Teams group
    result = await session.execute(
        select(OrganizationTeamsGroup).where(
            OrganizationTeamsGroup.organization_id == user.organization_id
        )
    )
    org_group = result.scalars().first()

    if org_group is None:
        return {
            "teams_user_id": user.teams_user_id,
            "org_team": None,
            "in_team": False,
            "membership": None,
        }

    if not user.teams_user_id:
        return {
            "teams_user_id": None,
            "org_team": {"id": org_group.external_id, "name": org_group.name},
            "in_team": False,
            "membership": None,
        }

    try:
        membership = await teams_adapter.get_user_team_membership(
            user.teams_user_id, org_group.external_id
        )
        return {
            "teams_user_id": user.teams_user_id,
            "org_team": {"id": org_group.external_id, "name": org_group.name},
            "in_team": membership is not None,
            "membership": membership,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams get_user_team_membership error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


@router.delete("/user/{user_id}/remove")
async def remove_user_from_teams_team(user_id: UUID, session: SessionDep):
    """
    Remove the user from their organization's Teams team.
    Finds their membership_id live from Graph API and removes them.
    Does NOT delete the Azure AD user.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.teams_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has not been provisioned to Teams yet",
        )

    result = await session.execute(
        select(OrganizationTeamsGroup).where(
            OrganizationTeamsGroup.organization_id == user.organization_id
        )
    )
    org_group = result.scalars().first()
    if org_group is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No Teams group configured for this user's organization",
        )

    try:
        membership = await teams_adapter.get_user_team_membership(
            user.teams_user_id, org_group.external_id
        )
        if membership is None:
            return {"removed": False, "detail": "User is not currently in the team"}

        removed = await teams_adapter.remove_member_from_team(
            org_group.external_id, membership["membership_id"]
        )
        return {"removed": removed, "detail": "User removed from Teams team" if removed else "Already removed"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams remove_user error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


# ── Admin: Azure AD user management ───────────────────────────────────────────

@router.get("/users")
async def list_azure_ad_users():
    """List all Azure AD users in the tenant (admin operation)."""
    try:
        return await teams_adapter.list_all_users()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Teams list_all_users error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")


@router.delete("/users/{user_object_id}")
async def delete_azure_ad_user(user_object_id: str):
    """
    Permanently delete an Azure AD user (admin operation).
    This deletes the user from Azure AD — use with caution.
    """
    try:
        await teams_adapter.delete_user(user_object_id)
        return {"detail": f"Azure AD user {user_object_id} deleted"}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("Teams delete_user error: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Teams error: {e}")
