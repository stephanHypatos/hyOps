"""
Microsoft Teams integration via Microsoft Graph API.

Uses OAuth 2.0 client credentials flow to authenticate as the registered
Azure AD application, then:
  1. Calls the invitation API (handles both new and existing guest users)
  2. Adds the user as a member of the specified Teams team

Required Azure app permissions (with admin consent):
    User.Invite.All           - to invite / look up guest users
    TeamMember.ReadWrite.All  - to add members to the Teams team

Credentials (set in .env):
    AZURE_TENANT_ID=
    AZURE_CLIENT_ID=
    AZURE_CLIENT_SECRET=
    TEAMS_TEAM_ID=        # Microsoft 365 Group / Team ID
"""

import asyncio

import httpx

from app.config import integration_settings

_TIMEOUT = 15


def _check_config() -> None:
    cfg = integration_settings
    missing = [
        name for name, val in [
            ("AZURE_TENANT_ID", cfg.AZURE_TENANT_ID),
            ("AZURE_CLIENT_ID", cfg.AZURE_CLIENT_ID),
            ("AZURE_CLIENT_SECRET", cfg.AZURE_CLIENT_SECRET),
            ("TEAMS_TEAM_ID", cfg.TEAMS_TEAM_ID),
        ] if not val
    ]
    if missing:
        raise RuntimeError(
            f"Teams integration not configured. Missing: {', '.join(missing)}"
        )


def _get_access_token_sync() -> str:
    cfg = integration_settings
    url = f"https://login.microsoftonline.com/{cfg.AZURE_TENANT_ID}/oauth2/v2.0/token"
    resp = httpx.post(url, data={
        "grant_type": "client_credentials",
        "client_id": cfg.AZURE_CLIENT_ID,
        "client_secret": cfg.AZURE_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_or_invite_user_sync(email: str, display_name: str, token: str) -> tuple:
    """
    Call the Graph invitations endpoint.
    - New user     → creates a B2B guest, returns their object ID.
    - Existing user → returns existing object ID without re-sending invite.
    Returns (user_object_id: str, newly_invited: bool).
    """
    resp = httpx.post(
        "https://graph.microsoft.com/v1.0/invitations",
        json={
            "invitedUserEmailAddress": email,
            "invitedUserDisplayName": display_name,
            "inviteRedirectUrl": "https://teams.microsoft.com",
            "sendInvitationMessage": False,
        },
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    user_id = data["invitedUser"]["id"]
    newly_invited = data.get("status") == "PendingAcceptance"
    return user_id, newly_invited


def _add_to_team_sync(team_id: str, user_object_id: str, token: str) -> None:
    """
    Add the user to the Teams team as a regular member.
    409 = already a member → treated as success (idempotent).
    """
    resp = httpx.post(
        f"https://graph.microsoft.com/v1.0/teams/{team_id}/members",
        json={
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": [],
            "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_object_id}')",
        },
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=_TIMEOUT,
    )
    if resp.status_code == 409:
        return  # already a member
    resp.raise_for_status()


def _add_user_to_teams_sync(email: str, display_name: str, team_id: str) -> dict:
    _check_config()
    token = _get_access_token_sync()
    user_object_id, newly_invited = _get_or_invite_user_sync(email, display_name, token)
    _add_to_team_sync(team_id, user_object_id, token)
    return {
        "teams_user_object_id": user_object_id,
        "teams_team_id": team_id,
        "teams_guest_invited": newly_invited,
    }


# ── Async public interface ────────────────────────────────────────────────────

async def add_user_to_teams(email: str, display_name: str, team_id: str) -> dict:
    """
    Invite the user to Azure AD (if not already there) and add them to the given Teams team.
    team_id: the OrganizationTeamsGroup.external_id for this org.
    """
    return await asyncio.to_thread(_add_user_to_teams_sync, email, display_name, team_id)
