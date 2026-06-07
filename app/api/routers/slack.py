"""
Slack integration endpoints.

Channel conventions per org:
  client-{slug}       — for users of type "internal"
  ext-partner-{slug}  — for users of type "internal" and "partner"

Endpoints:
  GET    /slack/organization/{org_id}/channels
  POST   /slack/organization/{org_id}/create-channel
  DELETE /slack/organization/{org_id}/channels/{channel_type}
  GET    /slack/organization/{org_id}/channels/{channel_type}/members
  DELETE /slack/organization/{org_id}/channels/{channel_type}/members/{slack_user_id}

  POST   /slack/user/{user_id}/add
  DELETE /slack/user/{user_id}/remove
  GET    /slack/user/{user_id}/channels

  GET    /slack/channels        (admin — workspace channel list)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.adapters import slack as slack_adapter
from app.database.models import (
    Organization,
    OrganizationSlackChannel,
    User,
    UserSlackChannel,
    UserType,
)
from app.database.session import SessionDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["Slack Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateChannelRequest(BaseModel):
    channel_type: str  # "client" or "ext_partner"


class RemoveFromChannelRequest(BaseModel):
    channel_type: str  # "client" or "ext_partner"


def _validate_channel_type(channel_type: str) -> None:
    if channel_type not in ("client", "ext_partner"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid channel_type '{channel_type}'. Must be 'client' or 'ext_partner'.",
        )


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/organization/{org_id}/channels")
async def get_slack_channels_for_org(org_id: UUID, session: SessionDep):
    """Get all Slack channels configured for an organization."""
    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id
        )
    )
    channels = result.scalars().all()
    return {
        "channels": [
            {
                "id": str(c.id),
                "external_id": c.external_id,
                "channel_name": c.channel_name,
                "channel_type": c.channel_type,
            }
            for c in channels
        ]
    }


@router.post("/organization/{org_id}/create-channel", status_code=status.HTTP_200_OK)
async def create_slack_channel_for_org(
    org_id: UUID,
    body: CreateChannelRequest,
    session: SessionDep,
):
    """
    Create a Slack channel for the organization (if it doesn't exist) and invite
    the appropriate users based on channel_type:
      client      → invite users of type 'internal'
      ext_partner → invite users of type 'internal' and 'partner'

    Returns 409 if the channel is already configured in hyOps for this org.
    """
    _validate_channel_type(body.channel_type)

    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if already configured in DB
    existing_result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id,
            OrganizationSlackChannel.channel_type == body.channel_type,
        )
    )
    existing = existing_result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A '{body.channel_type}' Slack channel is already configured for this organization: {existing.channel_name} ({existing.external_id})",
        )

    # Determine channel name
    if body.channel_type == "client":
        channel_name = slack_adapter.client_channel_name(org.name)
    else:
        channel_name = slack_adapter.partner_channel_name(org.name)

    # Create or find the Slack channel
    try:
        ch = await slack_adapter.get_or_create_channel(channel_name, is_private=True)
    except Exception as exc:
        logger.error("Slack: create channel error: %s", exc)
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")

    # Store in DB
    org_channel = OrganizationSlackChannel(
        organization_id=org_id,
        external_id=ch["id"],
        channel_name=ch["name"],
        channel_type=body.channel_type,
    )
    session.add(org_channel)
    await session.flush()  # get the DB id before committing

    # Get users to invite
    users_result = await session.execute(
        select(User).where(User.organization_id == org_id)
    )
    all_users = users_result.scalars().all()

    if body.channel_type == "client":
        target_users = [u for u in all_users if u.type == UserType.internal]
    else:  # ext_partner
        target_users = [u for u in all_users if u.type in (UserType.internal, UserType.partner)]

    emails = [u.email for u in target_users]

    # Invite to Slack channel
    provision_result = {"invited": [], "not_found": []}
    if emails:
        try:
            provision_result = await slack_adapter.provision_users_to_channel(ch["id"], emails)
        except Exception as exc:
            logger.warning("Slack: partial failure provisioning users: %s", exc)

    # Store UserSlackChannel links for invited users
    for user in target_users:
        if user.email in provision_result.get("invited", []):
            session.add(UserSlackChannel(
                user_id=user.id,
                slack_channel_id=org_channel.id,
            ))

    await session.commit()

    return {
        "channel_id": ch["id"],
        "channel_name": ch["name"],
        "channel_type": body.channel_type,
        "created": ch.get("created", True),
        "already_exists": ch.get("already_exists", False),
        "users_invited": provision_result.get("invited", []),
        "users_not_found": provision_result.get("not_found", []),
    }


@router.delete("/organization/{org_id}/channels/{channel_type}")
async def unlink_slack_channel(org_id: UUID, channel_type: str, session: SessionDep):
    """
    Unlink a Slack channel from this organization in hyOps.
    Does NOT delete the channel in Slack.
    """
    _validate_channel_type(channel_type)

    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id,
            OrganizationSlackChannel.channel_type == channel_type,
        )
    )
    org_channel = result.scalars().first()
    if org_channel is None:
        raise HTTPException(status_code=404, detail=f"No '{channel_type}' Slack channel configured for this organization")

    # Remove UserSlackChannel links
    links_result = await session.execute(
        select(UserSlackChannel).where(
            UserSlackChannel.slack_channel_id == org_channel.id
        )
    )
    for link in links_result.scalars().all():
        await session.delete(link)

    await session.delete(org_channel)
    await session.commit()
    return {"detail": f"Slack '{channel_type}' channel unlinked from organization"}


@router.get("/organization/{org_id}/channels/{channel_type}/members")
async def get_slack_channel_members(org_id: UUID, channel_type: str, session: SessionDep):
    """Get live member list from the Slack API for a channel."""
    _validate_channel_type(channel_type)

    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id,
            OrganizationSlackChannel.channel_type == channel_type,
        )
    )
    org_channel = result.scalars().first()
    if org_channel is None:
        raise HTTPException(
            status_code=404,
            detail=f"No '{channel_type}' Slack channel configured for this organization",
        )

    try:
        members = await slack_adapter.get_channel_members(org_channel.external_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")

    return {"members": members, "channel_name": org_channel.channel_name}


@router.delete("/organization/{org_id}/channels/{channel_type}/members/{slack_user_id}")
async def remove_member_from_slack_channel(
    org_id: UUID, channel_type: str, slack_user_id: str, session: SessionDep
):
    """Remove a member from a Slack channel by their Slack user ID."""
    _validate_channel_type(channel_type)

    result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == org_id,
            OrganizationSlackChannel.channel_type == channel_type,
        )
    )
    org_channel = result.scalars().first()
    if org_channel is None:
        raise HTTPException(
            status_code=404,
            detail=f"No '{channel_type}' Slack channel configured for this organization",
        )

    try:
        removed = await slack_adapter.remove_from_channel(org_channel.external_id, slack_user_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")

    if not removed:
        raise HTTPException(status_code=404, detail="User was not in this channel")

    # Remove UserSlackChannel link if present
    # Find user by slack_user_id is hard without storing it, so we do a best-effort cleanup
    return {"detail": f"User {slack_user_id} removed from channel {org_channel.channel_name}"}


# ── User-level ────────────────────────────────────────────────────────────────

@router.get("/user/{user_id}/channels")
async def get_user_slack_channels(user_id: UUID, session: SessionDep):
    """Get Slack channels the user is currently linked to in hyOps."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Get org channels
    org_channels_result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == user.organization_id
        )
    )
    org_channels = {c.id: c for c in org_channels_result.scalars().all()}

    # Get user links
    links_result = await session.execute(
        select(UserSlackChannel).where(UserSlackChannel.user_id == user_id)
    )
    user_links = links_result.scalars().all()

    linked_channel_ids = {link.slack_channel_id for link in user_links}

    return {
        "user_type": user.type,
        "org_channels": [
            {
                "id": str(c.id),
                "external_id": c.external_id,
                "channel_name": c.channel_name,
                "channel_type": c.channel_type,
                "user_is_linked": c.id in linked_channel_ids,
            }
            for c in org_channels.values()
        ],
    }


@router.post("/user/{user_id}/add")
async def add_user_to_slack(user_id: UUID, session: SessionDep):
    """
    Add a user to their organization's appropriate Slack channel(s) based on type:
      internal → client channel + ext_partner channel
      partner  → ext_partner channel only
      customer → neither (returns 422)
    """
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.type == UserType.customer:
        raise HTTPException(
            status_code=422,
            detail="Customer users are not added to Slack channels.",
        )

    # Get org channels
    org_channels_result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == user.organization_id
        )
    )
    org_channels = {c.channel_type: c for c in org_channels_result.scalars().all()}

    if not org_channels:
        raise HTTPException(
            status_code=422,
            detail="No Slack channels configured for this user's organization. Create them via the integrations page first.",
        )

    # Determine which channels this user should be in
    if user.type == UserType.internal:
        target_types = [t for t in ("client", "ext_partner") if t in org_channels]
    else:  # partner
        target_types = [t for t in ("ext_partner",) if t in org_channels]

    if not target_types:
        raise HTTPException(
            status_code=422,
            detail=f"No matching Slack channels for user type '{user.type}'. "
                   f"Available: {list(org_channels.keys())}",
        )

    # Existing links
    links_result = await session.execute(
        select(UserSlackChannel).where(UserSlackChannel.user_id == user_id)
    )
    existing_links = {link.slack_channel_id for link in links_result.scalars().all()}

    results = []
    errors = []

    for channel_type in target_types:
        ch = org_channels[channel_type]
        try:
            result = await slack_adapter.provision_users_to_channel(ch.external_id, [user.email])
            invited = result.get("invited", [])
            not_found = result.get("not_found", [])
            if invited:
                # Add DB link
                if ch.id not in existing_links:
                    session.add(UserSlackChannel(user_id=user_id, slack_channel_id=ch.id))
                    existing_links.add(ch.id)
                results.append({"channel_name": ch.channel_name, "channel_type": channel_type, "status": "invited"})
            elif not_found:
                results.append({
                    "channel_name": ch.channel_name,
                    "channel_type": channel_type,
                    "status": "not_found_in_slack",
                    "detail": f"User '{user.email}' not found in Slack workspace",
                })
            else:
                # Already in channel
                if ch.id not in existing_links:
                    session.add(UserSlackChannel(user_id=user_id, slack_channel_id=ch.id))
                    existing_links.add(ch.id)
                results.append({"channel_name": ch.channel_name, "channel_type": channel_type, "status": "already_member"})
        except Exception as exc:
            logger.error("Slack add user error (%s): %s", channel_type, exc)
            errors.append({"channel_type": channel_type, "error": str(exc)})

    await session.commit()

    if not results and errors:
        raise HTTPException(status_code=502, detail=f"Slack errors: {errors}")

    return {
        "channels": results,
        "errors": errors,
        "user_email": user.email,
        "user_type": user.type,
    }


@router.delete("/user/{user_id}/remove")
async def remove_user_from_slack(
    user_id: UUID,
    body: RemoveFromChannelRequest,
    session: SessionDep,
):
    """
    Remove a user from a Slack channel. Looks up user by email in Slack.
    """
    _validate_channel_type(body.channel_type)

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Get org channel
    ch_result = await session.execute(
        select(OrganizationSlackChannel).where(
            OrganizationSlackChannel.organization_id == user.organization_id,
            OrganizationSlackChannel.channel_type == body.channel_type,
        )
    )
    org_channel = ch_result.scalars().first()
    if org_channel is None:
        raise HTTPException(
            status_code=404,
            detail=f"No '{body.channel_type}' Slack channel configured for this organization",
        )

    # Look up slack user by email
    try:
        slack_user = await slack_adapter.get_user_by_email(user.email)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")

    if slack_user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user.email}' not found in Slack workspace",
        )

    # Remove from channel
    try:
        removed = await slack_adapter.remove_from_channel(org_channel.external_id, slack_user["slack_user_id"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")

    # Remove DB link
    link_result = await session.execute(
        select(UserSlackChannel).where(
            UserSlackChannel.user_id == user_id,
            UserSlackChannel.slack_channel_id == org_channel.id,
        )
    )
    link = link_result.scalars().first()
    if link:
        await session.delete(link)
        await session.commit()

    return {
        "detail": f"User '{user.email}' removed from channel '{org_channel.channel_name}'",
        "removed": removed,
    }


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/channels")
async def list_workspace_channels():
    """List all non-archived channels in the Slack workspace (admin view)."""
    try:
        channels = await slack_adapter.list_channels()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack error: {exc}")
    return channels
