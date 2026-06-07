"""
Microsoft Teams integration via Microsoft Graph API.

Full lifecycle:
  - Check if team exists by name
  - Create team (with admin owner, async polling until ready)
  - Get or invite a user (look up by email → invite if not found)
  - Add user to a Teams team
  - Remove member from a Teams team
  - List all teams in tenant
  - List all Azure AD users
  - Delete team (deletes underlying M365 group)
  - Delete Azure AD user

Required Azure app permissions (admin consent):
    Group.ReadWrite.All            — create/delete M365 groups / Teams
    User.ReadWrite.All             — create / delete users
    User.Invite.All                — send B2B invitations
    TeamMember.ReadWrite.All       — manage team members
    Directory.ReadWrite.All        — read directory objects

Credentials (set in .env):
    AZURE_TENANT_ID=
    AZURE_CLIENT_ID=
    AZURE_CLIENT_SECRET=
    TEAMS_ADMIN_USER_ID=02f15082-7848-48ac-830f-3af9db319dee   (default)
"""

import asyncio
import logging
import re
import time
from typing import Optional

import httpx

from app.config import integration_settings

_TIMEOUT = 30          # seconds per HTTP request
_POLL_INTERVAL = 5     # seconds between async-op polls
_POLL_MAX = 24         # max poll attempts (~120 s total) — MS can take up to 5 min
_BASE = "https://graph.microsoft.com/v1.0"

logger = logging.getLogger(__name__)


# ── Config helpers ────────────────────────────────────────────────────────────

def _check_config() -> None:
    cfg = integration_settings
    missing = [
        name for name, val in [
            ("AZURE_TENANT_ID", cfg.AZURE_TENANT_ID),
            ("AZURE_CLIENT_ID", cfg.AZURE_CLIENT_ID),
            ("AZURE_CLIENT_SECRET", cfg.AZURE_CLIENT_SECRET),
        ] if not val
    ]
    if missing:
        raise RuntimeError(
            f"Teams integration not configured. Missing env vars: {', '.join(missing)}"
        )


def _admin_user_id() -> str:
    return integration_settings.TEAMS_ADMIN_USER_ID


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_token_sync() -> str:
    cfg = integration_settings
    _check_config()
    url = f"https://login.microsoftonline.com/{cfg.AZURE_TENANT_ID}/oauth2/v2.0/token"
    resp = httpx.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     cfg.AZURE_CLIENT_ID,
        "client_secret": cfg.AZURE_CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Teams ─────────────────────────────────────────────────────────────────────

def _check_team_exists_sync(name: str, token: str) -> Optional[dict]:
    """Return {id, name} if a Teams team with this displayName already exists, else None."""
    logger.info("Teams: checking for existing team named '%s'", name)
    # OData filter: Teams-provisioned M365 groups with matching displayName
    escaped = name.replace("'", "''")
    resp = httpx.get(
        f"{_BASE}/groups",
        params={
            "$top": "999",
            "$filter": f"resourceProvisioningOptions/Any(x:x eq 'Team') and displayName eq '{escaped}'",
            "$select": "id,displayName,description",
        },
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    items = resp.json().get("value", [])
    if items:
        g = items[0]
        logger.info("Teams: found existing team '%s' (ID: %s)", g["displayName"], g["id"])
        return {"id": g["id"], "name": g["displayName"]}
    logger.info("Teams: no existing team found for '%s'", name)
    return None


def _extract_team_id_from_location(location: str) -> Optional[str]:
    """
    Extract the Teams team ID from a Content-Location header.
    Handles both forms:
      /teams('dbd8de4f-...')/operations('3a6fdece-...')
      /teams/dbd8de4f-.../operations/3a6fdece-...
    """
    # UUID pattern inside the path segment after /teams
    match = re.search(
        r"/teams[/(']([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        location,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return None


def _poll_async_op_sync(location: str, token: str) -> Optional[str]:
    """
    Poll a Graph async-operation URL until it succeeds or we give up.
    Returns targetResourceId (team ID) on success, None on timeout (non-fatal).
    """
    if location.startswith("/"):
        location = f"{_BASE}{location}"
    for attempt in range(_POLL_MAX):
        time.sleep(_POLL_INTERVAL)
        try:
            resp = httpx.get(
                location,
                headers={"Authorization": f"Bearer {token}"},
                timeout=_TIMEOUT,
            )
        except Exception as e:
            logger.warning("Teams: poll request failed (attempt %d): %s", attempt + 1, e)
            continue

        if resp.status_code == 404:
            logger.info("Teams: async op not ready yet (attempt %d/%d)", attempt + 1, _POLL_MAX)
            continue

        if resp.status_code not in (200, 201):
            logger.warning("Teams: poll returned %s (attempt %d)", resp.status_code, attempt + 1)
            continue

        data = resp.json()
        op_status = data.get("status", "")
        logger.info("Teams: async op status=%s (attempt %d/%d)", op_status, attempt + 1, _POLL_MAX)

        if op_status == "succeeded":
            return data.get("targetResourceId") or None
        if op_status in ("failed", "cancelled"):
            err = data.get("error", {})
            raise RuntimeError(f"Teams: team creation {op_status}: {err.get('message', 'Unknown error')}")
        # "inProgress" / "notStarted" — keep polling

    logger.warning("Teams: async op poll timed out after %ds — team may still be provisioning", _POLL_MAX * _POLL_INTERVAL)
    return None  # non-fatal — team ID was already extracted from Content-Location


def _create_team_sync(name: str, token: str) -> dict:
    """
    Create a new Teams team (admin user as owner).
    Returns {id, name, provisioning: bool}.
    `provisioning=True` means the team ID is known but MS is still setting it up.
    """
    payload = {
        "template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
        "displayName": name,
        "description": f"Team for {name} — created by hyOps",
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{_admin_user_id()}')",
            }
        ],
    }
    logger.info("Teams: creating team '%s'", name)
    resp = httpx.post(f"{_BASE}/teams", json=payload, headers=_h(token), timeout=_TIMEOUT)
    logger.info("Teams: create response status=%s headers=%s", resp.status_code, dict(resp.headers))

    if resp.status_code in (200, 201):
        # Synchronous success (rare but possible)
        data = resp.json()
        return {"id": data["id"], "name": data.get("displayName", name), "provisioning": False}

    if resp.status_code == 202:
        location = (
            resp.headers.get("Content-Location")
            or resp.headers.get("Location")
            or ""
        )
        logger.info("Teams: 202 Accepted, Content-Location='%s'", location)

        # ── Step 1: Extract team ID from the URL immediately ─────────────────
        # Microsoft encodes the team ID in Content-Location even before the team
        # is fully provisioned, e.g.:
        #   /teams('dbd8de4f-...')/operations('3a6fdece-...')
        team_id = _extract_team_id_from_location(location)
        if team_id:
            logger.info("Teams: team ID extracted from Content-Location: %s", team_id)
        else:
            logger.warning("Teams: could not parse team ID from Content-Location='%s'", location)

        # ── Step 2: Poll briefly to see if provisioning completes quickly ─────
        # If it completes within _POLL_MAX * _POLL_INTERVAL seconds, great.
        # If not, we already have the team_id from step 1, so we're not blocked.
        if location:
            polled_id = _poll_async_op_sync(location, token)
            if polled_id:
                team_id = polled_id
                logger.info("Teams: provisioning confirmed via poll, ID=%s", team_id)
                return {"id": team_id, "name": name, "provisioning": False}

        if not team_id:
            raise RuntimeError(
                "Teams: team creation returned 202 but could not determine team ID "
                "(no Content-Location / no UUID in URL)"
            )

        # Team ID known but provisioning still in progress
        logger.info("Teams: returning team ID=%s (provisioning still in progress)", team_id)
        return {"id": team_id, "name": name, "provisioning": True}

    # Any other status code is an error
    try:
        err_body = resp.json()
    except Exception:
        err_body = resp.text
    logger.error("Teams: create team failed status=%s body=%s", resp.status_code, err_body)
    resp.raise_for_status()
    raise RuntimeError("Teams: unexpected status code")


def _list_teams_sync(token: str) -> list:
    """List all Teams teams in the tenant."""
    resp = httpx.get(
        f"{_BASE}/groups",
        params={
            "$top": "999",
            "$filter": "resourceProvisioningOptions/Any(x:x eq 'Team')",
            "$select": "id,displayName,description",
        },
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "id": g["id"],
            "name": g.get("displayName", ""),
            "description": g.get("description", ""),
        }
        for g in resp.json().get("value", [])
    ]


def _delete_team_sync(team_id: str, token: str) -> None:
    """Delete a Teams team by deleting its underlying M365 group."""
    resp = httpx.delete(f"{_BASE}/groups/{team_id}", headers=_h(token), timeout=_TIMEOUT)
    if resp.status_code == 404:
        raise RuntimeError(f"Team/group {team_id} not found in Azure AD")
    resp.raise_for_status()
    logger.info("Teams: deleted team/group %s", team_id)


# ── Users ─────────────────────────────────────────────────────────────────────

def _get_user_by_email_sync(email: str, token: str) -> Optional[dict]:
    """Look up an Azure AD user by email. Checks `mail` then `userPrincipalName`. Returns user dict or None."""
    normalized = email.strip().lower()
    for field in ("mail", "userPrincipalName"):
        try:
            resp = httpx.get(
                f"{_BASE}/users",
                params={
                    "$filter": f"{field} eq '{normalized}'",
                    "$select": "id,displayName,mail,userPrincipalName,accountEnabled",
                },
                headers=_h(token),
                timeout=_TIMEOUT,
            )
            if resp.status_code == 200:
                items = resp.json().get("value", [])
                if items:
                    u = items[0]
                    logger.info("Teams: found existing user '%s' via %s (ID: %s)", email, field, u["id"])
                    return {
                        "id": u["id"],
                        "display_name": u.get("displayName", email),
                        "email": u.get("mail") or u.get("userPrincipalName", email),
                    }
        except Exception:
            pass
    return None


def _invite_user_sync(email: str, display_name: str, token: str) -> dict:
    """Invite a user to Azure AD as a B2B guest. Returns {id, display_name, email, newly_invited}."""
    resp = httpx.post(
        f"{_BASE}/invitations",
        json={
            "invitedUserEmailAddress": email,
            "invitedUserDisplayName": display_name,
            "inviteRedirectUrl": "https://teams.microsoft.com",
            "sendInvitationMessage": True,
        },
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    user_id = data["invitedUser"]["id"]
    newly_invited = data.get("status") == "PendingAcceptance"
    logger.info("Teams: invited user '%s' (ID: %s, newly_invited=%s)", email, user_id, newly_invited)
    return {"id": user_id, "display_name": display_name, "email": email, "newly_invited": newly_invited}


def _get_or_invite_user_sync(email: str, display_name: str, token: str) -> dict:
    """Check if user exists in Azure AD; invite if not. Returns {id, display_name, email, newly_invited}."""
    existing = _get_user_by_email_sync(email, token)
    if existing:
        existing["newly_invited"] = False
        return existing
    return _invite_user_sync(email, display_name, token)


def _add_user_to_team_sync(team_id: str, user_object_id: str, token: str, role: str = "member") -> None:
    """Add a user to a Teams team. 409 = already a member → idempotent."""
    roles_payload: list = ["owner"] if role == "owner" else []
    resp = httpx.post(
        f"{_BASE}/teams/{team_id}/members",
        json={
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": roles_payload,
            "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_object_id}')",
        },
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    if resp.status_code == 409:
        logger.info("Teams: user %s already a member of team %s", user_object_id, team_id)
        return
    resp.raise_for_status()
    logger.info("Teams: added user %s to team %s as %s", user_object_id, team_id, role)


def _get_team_members_sync(team_id: str, token: str) -> list:
    """Get all members of a Teams team."""
    resp = httpx.get(f"{_BASE}/teams/{team_id}/members", headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    members = []
    for m in resp.json().get("value", []):
        members.append({
            "membership_id": m.get("id", ""),
            "user_object_id": m.get("userId", ""),
            "display_name": m.get("displayName", ""),
            "email": m.get("email", ""),
            "roles": m.get("roles", []),
        })
    return members


def _remove_member_from_team_sync(team_id: str, membership_id: str, token: str) -> bool:
    """Remove a member from a team using their Teams membership ID."""
    resp = httpx.delete(
        f"{_BASE}/teams/{team_id}/members/{membership_id}",
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    if resp.status_code == 404:
        return False
    resp.raise_for_status()
    logger.info("Teams: removed membership %s from team %s", membership_id, team_id)
    return True


def _list_all_users_sync(token: str) -> list:
    """List Azure AD users (top 999)."""
    resp = httpx.get(
        f"{_BASE}/users",
        params={"$top": "999", "$select": "id,displayName,mail,userPrincipalName,accountEnabled"},
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "id": u["id"],
            "display_name": u.get("displayName", ""),
            "email": u.get("mail") or u.get("userPrincipalName", ""),
            "account_enabled": u.get("accountEnabled", True),
        }
        for u in resp.json().get("value", [])
    ]


def _delete_user_sync(user_object_id: str, token: str) -> None:
    """Delete an Azure AD user permanently."""
    resp = httpx.delete(f"{_BASE}/users/{user_object_id}", headers=_h(token), timeout=_TIMEOUT)
    if resp.status_code == 404:
        raise RuntimeError(f"Azure AD user {user_object_id} not found")
    resp.raise_for_status()
    logger.info("Teams: deleted Azure AD user %s", user_object_id)


# ── Compound sync helpers (token + operation in one thread) ───────────────────

def _provision_user_to_team_sync(email: str, display_name: str, team_id: str) -> dict:
    """Get-or-invite user, then add them to the team. Returns provision info."""
    _check_config()
    token = _get_token_sync()
    user = _get_or_invite_user_sync(email, display_name, token)
    # Small delay after invitation to let Azure AD propagate the new guest object
    if user.get("newly_invited"):
        time.sleep(2)
    _add_user_to_team_sync(team_id, user["id"], token)
    return {
        "teams_user_object_id": user["id"],
        "teams_team_id": team_id,
        "teams_guest_invited": user.get("newly_invited", False),
        "display_name": user.get("display_name", display_name),
    }


def _create_or_get_team_sync(name: str) -> dict:
    """Check for duplicate → create (or return existing). Returns {id, name, created, already_exists}."""
    _check_config()
    token = _get_token_sync()
    existing = _check_team_exists_sync(name, token)
    if existing:
        return {"id": existing["id"], "name": existing["name"], "created": False, "already_exists": True}
    team = _create_team_sync(name, token)
    return {"id": team["id"], "name": team["name"], "created": True, "already_exists": False}


def _get_user_team_membership_sync(teams_user_id: str, team_id: str, token: str) -> Optional[dict]:
    """Return the user's Teams membership record in the given team, or None if not a member."""
    members = _get_team_members_sync(team_id, token)
    for m in members:
        if m["user_object_id"] == teams_user_id:
            return m
    return None


# ── Async public interface ────────────────────────────────────────────────────

async def check_team_exists(name: str) -> Optional[dict]:
    """Return {id, name} if a team with this name exists, else None."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _check_team_exists_sync(name, token)
    return await asyncio.to_thread(_run)


async def create_team_for_org(name: str) -> dict:
    """
    Check for duplicate → create team.
    Returns {id, name, created, already_exists}.
    Raises RuntimeError if creation fails.
    """
    return await asyncio.to_thread(_create_or_get_team_sync, name)


async def list_teams() -> list:
    """List all Teams teams in the tenant."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _list_teams_sync(token)
    return await asyncio.to_thread(_run)


async def delete_team(team_id: str) -> None:
    """Delete a Teams team (deletes underlying M365 group)."""
    def _run():
        _check_config()
        token = _get_token_sync()
        _delete_team_sync(team_id, token)
    await asyncio.to_thread(_run)


async def get_user_by_email(email: str) -> Optional[dict]:
    """Look up an Azure AD user by email. Returns user dict or None."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _get_user_by_email_sync(email, token)
    return await asyncio.to_thread(_run)


async def provision_user_to_team(email: str, display_name: str, team_id: str) -> dict:
    """Get-or-invite user then add to team. Returns provision info dict."""
    return await asyncio.to_thread(_provision_user_to_team_sync, email, display_name, team_id)


async def get_team_members(team_id: str) -> list:
    """Get all members of a Teams team (live from Graph API)."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _get_team_members_sync(team_id, token)
    return await asyncio.to_thread(_run)


async def remove_member_from_team(team_id: str, membership_id: str) -> bool:
    """Remove a member from a team by their Teams membership ID."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _remove_member_from_team_sync(team_id, membership_id, token)
    return await asyncio.to_thread(_run)


async def get_user_team_membership(teams_user_id: str, team_id: str) -> Optional[dict]:
    """Return user's Teams membership record in the team, or None if not a member."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _get_user_team_membership_sync(teams_user_id, team_id, token)
    return await asyncio.to_thread(_run)


async def list_all_users() -> list:
    """List all Azure AD users in the tenant (top 999)."""
    def _run():
        _check_config()
        token = _get_token_sync()
        return _list_all_users_sync(token)
    return await asyncio.to_thread(_run)


async def delete_user(user_object_id: str) -> None:
    """Permanently delete an Azure AD user."""
    def _run():
        _check_config()
        token = _get_token_sync()
        _delete_user_sync(user_object_id, token)
    await asyncio.to_thread(_run)


# ── Backward compat ───────────────────────────────────────────────────────────

async def add_user_to_teams(email: str, display_name: str, team_id: str) -> dict:
    """Legacy alias for provision_user_to_team."""
    return await provision_user_to_team(email, display_name, team_id)
