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

_TIMEOUT = 30   # seconds per HTTP request
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


def _create_team_sync(name: str, token: str) -> dict:
    """
    Create a new Teams team (admin user as owner). Returns {id, name} immediately.

    MS Graph returns 202 Accepted — team provisioning continues on Microsoft's
    servers asynchronously. The team ID is embedded in the Content-Location header
    right away, so we extract it and return without polling/waiting.
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
    logger.info("Teams: create response status=%s", resp.status_code)

    # Synchronous success (rare but handle it)
    if resp.status_code in (200, 201):
        data = resp.json()
        logger.info("Teams: team '%s' created synchronously (ID: %s)", name, data["id"])
        return {"id": data["id"], "name": data.get("displayName", name)}

    # Standard async path — 202 Accepted
    if resp.status_code == 202:
        location = (
            resp.headers.get("Content-Location")
            or resp.headers.get("Location")
            or ""
        )
        logger.info("Teams: 202 Accepted — Content-Location: '%s'", location)

        # The team ID is embedded in the Content-Location URL immediately, e.g.:
        #   /teams('dbd8de4f-5d47-46da-887d-90c703cfa1ac')/operations('3a6fde...')
        # Extract it — no polling needed.
        team_id = _extract_team_id_from_location(location)
        if team_id:
            logger.info("Teams: team '%s' queued for provisioning (ID: %s)", name, team_id)
            return {"id": team_id, "name": name}

        # Fallback: Content-Location didn't contain a UUID (shouldn't happen, but be safe).
        # Wait 5 s then search by name — much faster than full polling.
        logger.warning("Teams: no UUID in Content-Location='%s', falling back to name search", location)
        time.sleep(5)
        existing = _check_team_exists_sync(name, token)
        if existing:
            logger.info("Teams: found team '%s' by name (ID: %s)", name, existing["id"])
            return {"id": existing["id"], "name": existing["name"]}

        raise RuntimeError(
            f"Teams: team '{name}' was submitted but we could not determine its ID. "
            "Check Microsoft Teams directly and use 'Link existing team' to connect it."
        )

    # Any other status is an error
    try:
        err_body = resp.json()
    except Exception:
        err_body = resp.text
    logger.error("Teams: create team failed status=%s body=%s", resp.status_code, err_body)
    resp.raise_for_status()
    raise RuntimeError("Teams: unexpected response")


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


def _add_user_to_group_sync(group_id: str, user_object_id: str, token: str) -> None:
    """
    Add a user to the M365 group that backs the Teams team.
    Uses POST /groups/{group_id}/members/$ref — works for external/guest users
    and only requires Group.ReadWrite.All (not TeamMember.ReadWrite.All).
    Idempotent: 400 "already exist" and 409 are treated as success.
    """
    resp = httpx.post(
        f"{_BASE}/groups/{group_id}/members/$ref",
        json={"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_object_id}"},
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    if resp.status_code == 204:
        logger.info("Teams: added user %s to group %s", user_object_id, group_id)
        return
    if resp.status_code == 409:
        logger.info("Teams: user %s already in group %s (409)", user_object_id, group_id)
        return
    if resp.status_code == 400:
        try:
            msg = resp.json().get("error", {}).get("message", "")
            if "already exist" in msg.lower():
                logger.info("Teams: user %s already in group %s (400 already exists)", user_object_id, group_id)
                return
        except Exception:
            pass
    resp.raise_for_status()


def _get_team_members_sync(group_id: str, token: str) -> list:
    """
    Get all members of the M365 group that backs the Teams team.
    Uses GET /groups/{group_id}/members (Groups API, not Teams members API).
    Returns user_object_id as the membership_id so the Remove button can call
    DELETE /groups/{group_id}/members/{user_object_id}/$ref.
    """
    resp = httpx.get(
        f"{_BASE}/groups/{group_id}/members",
        params={"$select": "id,displayName,mail,userPrincipalName"},
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    members = []
    for m in resp.json().get("value", []):
        obj_id = m.get("id", "")
        email = m.get("mail") or m.get("userPrincipalName", "")
        members.append({
            "membership_id": obj_id,   # used by the Remove button
            "user_object_id": obj_id,
            "display_name": m.get("displayName", ""),
            "email": email,
            "roles": [],               # Groups API doesn't return team-specific roles
        })
    return members


def _remove_member_from_team_sync(group_id: str, user_object_id: str, token: str) -> bool:
    """
    Remove a user from the M365 group using DELETE /groups/{group_id}/members/{user_object_id}/$ref.
    The `user_object_id` is the Azure AD object ID (same value returned as membership_id
    by _get_team_members_sync).
    """
    resp = httpx.delete(
        f"{_BASE}/groups/{group_id}/members/{user_object_id}/$ref",
        headers=_h(token),
        timeout=_TIMEOUT,
    )
    if resp.status_code == 404:
        return False
    resp.raise_for_status()
    logger.info("Teams: removed user %s from group %s", user_object_id, group_id)
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

def _provision_user_to_team_sync(email: str, display_name: str, group_id: str) -> dict:
    """
    Full user provisioning flow:
      1. Check if user already exists in Azure AD by email
      2. If not → POST /invitations (B2B guest invite, sends email)
      3. POST /groups/{group_id}/members/$ref  (Groups API — no TeamMember permission needed)
    """
    _check_config()
    token = _get_token_sync()
    user = _get_or_invite_user_sync(email, display_name, token)
    # Brief delay after a fresh invitation — Azure AD needs a moment to propagate the guest object
    if user.get("newly_invited"):
        logger.info("Teams: new guest invited, waiting 3s for Azure AD propagation…")
        time.sleep(3)
    _add_user_to_group_sync(group_id, user["id"], token)
    return {
        "teams_user_object_id": user["id"],
        "teams_team_id": group_id,
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


def _get_user_team_membership_sync(teams_user_id: str, group_id: str, token: str) -> Optional[dict]:
    """Return the user's group membership record, or None if not a member."""
    members = _get_team_members_sync(group_id, token)
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
