"""
Slack integration via Slack Web API.

Channel conventions:
  client-{org_slug}       — for users of type "internal"
  ext-partner-{org_slug}  — for users of type "internal" and "partner"

Required bot token scopes (OAuth & Permissions → Bot Token Scopes):
  channels:manage   create / invite / remove members (public channels)
  channels:read     list public channels
  groups:write      create / invite / remove members (private channels)
  groups:read       list private channels
  users:read        look up workspace users
  users:read.email  look up users by email address

Credentials (.env):
  SLACK_BOT_TOKEN=xoxb-...   (Bot User OAuth Token from your Slack app settings)
"""

import asyncio
import logging
import re
from typing import Optional

import httpx

from app.config import integration_settings

_BASE = "https://slack.com/api"
_TIMEOUT = 15

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _token() -> str:
    return integration_settings.SLACK_BOT_TOKEN or ""


def _check_config() -> None:
    if not _token():
        raise RuntimeError(
            "SLACK_BOT_TOKEN is not configured. "
            "Add it to .env: SLACK_BOT_TOKEN=xoxb-..."
        )


def _headers() -> dict:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def _get(method: str, params: Optional[dict] = None) -> dict:
    resp = httpx.get(
        f"{_BASE}/{method}",
        headers={"Authorization": f"Bearer {_token()}"},
        params=params or {},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack {method}: {data.get('error', 'unknown_error')}")
    return data


def _post(method: str, payload: dict) -> dict:
    resp = httpx.post(
        f"{_BASE}/{method}",
        headers=_headers(),
        json=payload,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        err = data.get("error", "unknown_error")
        # Treat these as non-fatal — caller decides
        raise RuntimeError(f"Slack {method}: {err}")
    return data


def slugify(org_name: str) -> str:
    """Convert an org name to a valid Slack channel name segment.
    Slack rules: lowercase, letters/numbers/hyphens only, max 80 chars total (with prefix).
    """
    slug = org_name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)  # non-alphanumeric → hyphen
    slug = slug.strip("-")                    # remove leading/trailing hyphens
    return slug[:60]                          # leave room for prefix


def client_channel_name(org_name: str) -> str:
    """Channel for internal users: client-{org_slug}"""
    return f"client-{slugify(org_name)}"


def partner_channel_name(org_name: str) -> str:
    """Channel for internal + partner users: ext-partner-{org_slug}"""
    return f"ext-partner-{slugify(org_name)}"


# ── Channels ──────────────────────────────────────────────────────────────────

def _find_channel_by_name_sync(name: str) -> Optional[dict]:
    """Search all channels (public + private) for one matching `name`. Returns {id, name} or None."""
    _check_config()
    cursor = None
    while True:
        params: dict = {
            "types": "public_channel,private_channel",
            "limit": 200,
            "exclude_archived": "true",
        }
        if cursor:
            params["cursor"] = cursor
        data = _get("conversations.list", params)
        for ch in data.get("channels", []):
            if ch.get("name") == name:
                logger.info("Slack: found existing channel '%s' (ID: %s)", name, ch["id"])
                return {"id": ch["id"], "name": ch["name"]}
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break
    logger.info("Slack: channel '%s' not found", name)
    return None


def _create_channel_sync(name: str, is_private: bool = True) -> dict:
    """Create a new Slack channel. Returns {id, name}."""
    _check_config()
    logger.info("Slack: creating channel '%s' (private=%s)", name, is_private)
    data = _post("conversations.create", {"name": name, "is_private": is_private})
    ch = data["channel"]
    logger.info("Slack: channel '%s' created (ID: %s)", ch["name"], ch["id"])
    return {"id": ch["id"], "name": ch["name"]}


def _list_channels_sync() -> list:
    """List all non-archived channels in the workspace."""
    _check_config()
    channels = []
    cursor = None
    while True:
        params: dict = {
            "types": "public_channel,private_channel",
            "limit": 200,
            "exclude_archived": "true",
        }
        if cursor:
            params["cursor"] = cursor
        data = _get("conversations.list", params)
        for ch in data.get("channels", []):
            channels.append({
                "id": ch["id"],
                "name": ch.get("name", ""),
                "is_private": ch.get("is_private", False),
                "num_members": ch.get("num_members", 0),
            })
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break
    return channels


# ── Users ─────────────────────────────────────────────────────────────────────

def _get_user_by_email_sync(email: str) -> Optional[dict]:
    """Look up a Slack user by email. Returns {slack_user_id, name, email} or None."""
    _check_config()
    try:
        data = _get("users.lookupByEmail", {"email": email.strip().lower()})
        u = data["user"]
        return {
            "slack_user_id": u["id"],
            "name": u.get("real_name") or u.get("name", email),
            "email": email,
        }
    except RuntimeError as e:
        if "users_not_found" in str(e):
            logger.info("Slack: user '%s' not found in workspace", email)
            return None
        raise


def _invite_to_channel_sync(channel_id: str, user_ids: list[str]) -> None:
    """Invite a list of Slack user IDs to a channel. Batches by 30."""
    if not user_ids:
        return
    for i in range(0, len(user_ids), 30):
        batch = user_ids[i : i + 30]
        try:
            _post("conversations.invite", {"channel": channel_id, "users": ",".join(batch)})
            logger.info("Slack: invited batch of %d users to %s", len(batch), channel_id)
        except RuntimeError as e:
            err = str(e)
            if "already_in_channel" in err:
                logger.info("Slack: some users already in channel %s (OK)", channel_id)
            elif "cant_invite_self" in err:
                logger.info("Slack: skipping bot self-invite")
            else:
                raise


def _remove_from_channel_sync(channel_id: str, slack_user_id: str) -> bool:
    """Remove a user from a Slack channel. Returns True on success."""
    try:
        _post("conversations.kick", {"channel": channel_id, "user": slack_user_id})
        logger.info("Slack: removed user %s from channel %s", slack_user_id, channel_id)
        return True
    except RuntimeError as e:
        if "not_in_channel" in str(e):
            return False
        raise


def _get_channel_members_sync(channel_id: str) -> list:
    """Get all human members of a Slack channel with name + email."""
    _check_config()
    # 1. Get member IDs
    member_ids = []
    cursor = None
    while True:
        params: dict = {"channel": channel_id, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = _get("conversations.members", params)
        member_ids.extend(data.get("members", []))
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

    # 2. Enrich with user info (skip bots and deleted)
    members = []
    for uid in member_ids:
        try:
            data = _get("users.info", {"user": uid})
            u = data["user"]
            if u.get("is_bot") or u.get("deleted"):
                continue
            members.append({
                "slack_user_id": uid,
                "name": u.get("real_name") or u.get("name", uid),
                "email": u.get("profile", {}).get("email", ""),
            })
        except Exception as exc:
            logger.warning("Slack: could not get info for user %s: %s", uid, exc)
    return members


# ── Compound operations ───────────────────────────────────────────────────────

def _get_or_create_channel_sync(name: str, is_private: bool = True) -> dict:
    """Find channel by name or create it. Returns {id, name, created: bool}."""
    existing = _find_channel_by_name_sync(name)
    if existing:
        return {**existing, "created": False, "already_exists": True}
    channel = _create_channel_sync(name, is_private=is_private)
    return {**channel, "created": True, "already_exists": False}


def _provision_users_to_channel_sync(channel_id: str, emails: list[str]) -> dict:
    """
    Look up each email in Slack, invite found users to the channel.
    Returns {invited: [...], not_found: [...]}.
    """
    invited = []
    not_found = []
    user_ids = []

    for email in emails:
        user = _get_user_by_email_sync(email)
        if user:
            user_ids.append(user["slack_user_id"])
            invited.append(email)
        else:
            not_found.append(email)

    if user_ids:
        _invite_to_channel_sync(channel_id, user_ids)

    return {"invited": invited, "not_found": not_found}


# ── Async public interface ────────────────────────────────────────────────────

async def find_channel_by_name(name: str) -> Optional[dict]:
    return await asyncio.to_thread(_find_channel_by_name_sync, name)


async def get_or_create_channel(name: str, is_private: bool = True) -> dict:
    return await asyncio.to_thread(_get_or_create_channel_sync, name, is_private)


async def list_channels() -> list:
    return await asyncio.to_thread(_list_channels_sync)


async def get_user_by_email(email: str) -> Optional[dict]:
    return await asyncio.to_thread(_get_user_by_email_sync, email)


async def invite_to_channel(channel_id: str, user_ids: list[str]) -> None:
    await asyncio.to_thread(_invite_to_channel_sync, channel_id, user_ids)


async def remove_from_channel(channel_id: str, slack_user_id: str) -> bool:
    return await asyncio.to_thread(_remove_from_channel_sync, channel_id, slack_user_id)


async def get_channel_members(channel_id: str) -> list:
    return await asyncio.to_thread(_get_channel_members_sync, channel_id)


async def provision_users_to_channel(channel_id: str, emails: list[str]) -> dict:
    return await asyncio.to_thread(_provision_users_to_channel_sync, channel_id, emails)
