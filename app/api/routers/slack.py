"""
Slack integration endpoints.

Org-level:   PUT  /slack/organization/{org_id}/channel
User-level:  POST /slack/user/{user_id}/add

Note: The actual Slack API adapter is a stub — wire up app/adapters/slack.py
when Slack app credentials are available.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.database.models import (
    Organization,
    OrganizationSlackChannel,
    User,
    UserSlackChannel,
)
from app.database.session import SessionDep

router = APIRouter(prefix="/slack", tags=["Slack Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class SlackChannelAssign(BaseModel):
    external_id: str   # Slack channel ID (e.g. C01234ABCDE)
    channel_name: str


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/organization/{org_id}/channel")
async def get_slack_channel_for_org(org_id: UUID, session: SessionDep):
    """Get the Slack channel configured for an organization."""
    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id
        )
    )
    channel = result.scalars().first()
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Slack channel configured for this organization")
    return {"external_id": channel.external_id, "channel_name": channel.channel_name, "id": str(channel.id)}


@router.put("/organization/{org_id}/channel")
async def assign_slack_channel_to_org(
    org_id: UUID,
    body: SlackChannelAssign,
    session: SessionDep,
):
    """Assign (or update) a Slack channel for an organization."""
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.external_id = body.external_id
        existing.channel_name = body.channel_name
        session.add(existing)
    else:
        session.add(OrganizationSlackChannel(
            organization_id=org_id,
            external_id=body.external_id,
            channel_name=body.channel_name,
        ))

    await session.commit()
    return {"detail": f"Slack channel '{body.channel_name}' assigned to organization"}


# ── User-level ────────────────────────────────────────────────────────────────

@router.post("/user/{user_id}/add")
async def add_user_to_slack(user_id: UUID, session: SessionDep):
    """
    Add the user to the organization's configured Slack channel.
    Saves the UserSlackChannel link in the database.

    Note: Slack API call is stubbed — implement app/adapters/slack.py with
    Slack Web API (conversations.invite) when credentials are available.
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == user.organization_id
        )
    )
    org_channel = result.scalars().first()
    if org_channel is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No Slack channel configured for this user's organization. "
                   "Set one via PUT /slack/organization/{org_id}/channel first.",
        )

    # Create UserSlackChannel link if not already present
    link_result = await session.execute(
        select(UserSlackChannel).where(
            UserSlackChannel.user_id == user_id,
            UserSlackChannel.slack_channel_id == org_channel.id,
        )
    )
    if link_result.scalars().first() is None:
        session.add(UserSlackChannel(user_id=user_id, slack_channel_id=org_channel.id))
        await session.commit()

    # TODO: call Slack Web API here (conversations.invite) once adapter is implemented
    return {
        "detail": "User linked to Slack channel (API call stubbed)",
        "slack_channel": org_channel.channel_name,
        "slack_channel_id": org_channel.external_id,
        "user_email": user.email,
    }
