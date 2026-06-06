"""
Metabase integration — user provisioning and permission group membership management.

Authentication: API key sent as `x-api-key` header (requires Metabase v0.46+).

Credentials (set in .env):
    METABASE_URL=https://your-instance.metabase.com
    METABASE_API_KEY=mb_your_api_key_here
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import integration_settings

_TIMEOUT = 30  # seconds — Metabase can be slow on writes
_SYSTEM_GROUP_IDS = {1, 2}  # All Users, Administrators — never shown in UI

logger = logging.getLogger(__name__)


def _base() -> str:
    return (integration_settings.METABASE_URL or "").rstrip("/")


def _headers() -> dict:
    return {
        "x-api-key": integration_settings.METABASE_API_KEY or "",
        "Content-Type": "application/json",
    }


def _check_config() -> None:
    if not _base():
        raise RuntimeError("METABASE_URL is not configured")
    if not integration_settings.METABASE_API_KEY:
        raise RuntimeError("METABASE_API_KEY is not configured")


# ── Sync helpers (wrapped with asyncio.to_thread at call site) ───────────────

def _get_user_by_email_sync(email: str) -> Optional[dict]:
    resp = httpx.get(
        f"{_base()}/api/user",
        params={"query": email},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    users = data["data"] if isinstance(data, dict) and "data" in data else data
    normalized = email.strip().lower()
    for u in users:
        if u.get("email", "").strip().lower() == normalized:
            return u
    return None


def _create_user_sync(email: str, firstname: str, lastname: str) -> dict:
    resp = httpx.post(
        f"{_base()}/api/user",
        json={"email": email, "first_name": firstname, "last_name": lastname},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _list_groups_sync() -> list:
    _check_config()
    resp = httpx.get(
        f"{_base()}/api/permissions/group",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    groups = resp.json()
    return [
        {"id": g["id"], "name": g["name"]}
        for g in groups
        if g["id"] not in _SYSTEM_GROUP_IDS
    ]


def _add_to_group_sync(user_id: int, group_id: int) -> None:
    resp = httpx.post(
        f"{_base()}/api/permissions/membership",
        json={"group_id": group_id, "user_id": user_id},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    if resp.status_code in (200, 201):
        return
    if resp.status_code == 400:
        try:
            detail = resp.json().get("message", resp.text)
        except Exception:
            detail = resp.text
        if "already" in str(detail).lower():
            return  # idempotent — user already in group
        raise RuntimeError(f"Metabase refused membership (400): {detail}")
    resp.raise_for_status()


def _find_membership_id_sync(mb_user_id: int, group_id: int) -> Optional[int]:
    resp = httpx.get(
        f"{_base()}/api/permissions/membership",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    members = data.get(str(mb_user_id), [])
    for m in members:
        if m.get("group_id") == group_id:
            return m.get("membership_id")
    return None


def _remove_from_group_sync(mb_user_id: int, group_id: int) -> bool:
    membership_id = _find_membership_id_sync(mb_user_id, group_id)
    if membership_id is None:
        return False
    resp = httpx.delete(
        f"{_base()}/api/permissions/membership/{membership_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return True


def _get_user_memberships_sync(mb_user_id: int) -> list:
    user_resp = httpx.get(
        f"{_base()}/api/user/{mb_user_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    user_resp.raise_for_status()
    raw_memberships = user_resp.json().get("user_group_memberships", [])
    if not raw_memberships:
        return []

    groups_resp = httpx.get(
        f"{_base()}/api/permissions/group",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    groups_resp.raise_for_status()
    group_names = {g["id"]: g["name"] for g in groups_resp.json()}

    seen: set = set()
    result = []
    for m in raw_memberships:
        group_id = m.get("id")
        if group_id is None or group_id in _SYSTEM_GROUP_IDS:
            continue
        if group_id not in group_names:
            continue
        if group_id in seen:
            continue
        seen.add(group_id)
        result.append({"group_id": group_id, "group_name": group_names[group_id]})
    return result


def _get_group_by_name_sync(name: str) -> Optional[dict]:
    """
    Return the Metabase group dict if a group with that exact name already exists,
    or None if it doesn't. Case-insensitive comparison.
    """
    _check_config()
    logger.info("Metabase: checking for existing group named '%s'", name)
    resp = httpx.get(
        f"{_base()}/api/permissions/group",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    normalized = name.strip().lower()
    for g in resp.json():
        if g.get("name", "").strip().lower() == normalized:
            logger.info("Metabase: found existing group '%s' (ID: %s)", g["name"], g["id"])
            return {"id": g["id"], "name": g["name"]}
    logger.info("Metabase: no existing group found for '%s'", name)
    return None


def _create_group_sync(name: str) -> dict:
    """
    Create a new Metabase permission group.
    Returns: {id, name}
    Raises RuntimeError if a group with that name already exists.
    """
    _check_config()
    existing = _get_group_by_name_sync(name)
    if existing:
        raise RuntimeError(
            f"DUPLICATE_GROUP:{existing['id']}:{existing['name']}"
        )
    logger.info("Metabase: creating group '%s'", name)
    resp = httpx.post(
        f"{_base()}/api/permissions/group",
        json={"name": name},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    logger.info("Metabase: create group response status=%s", resp.status_code)
    resp.raise_for_status()
    data = resp.json()
    logger.info("Metabase: group created — ID=%s name='%s'", data["id"], data["name"])
    return {"id": data["id"], "name": data["name"]}


def _provision_user_sync(email: str, firstname: str, lastname: str, group_id: int) -> dict:
    """
    Ensure the user exists in Metabase and is a member of the given permission group.
    Returns: {email, metabase_user_id, metabase_group_id, user_exists, created}
    """
    _check_config()
    normalized = email.strip().lower()
    existing = _get_user_by_email_sync(normalized)
    if existing:
        _add_to_group_sync(existing["id"], group_id)
        return {
            "email": normalized,
            "metabase_user_id": existing["id"],
            "metabase_group_id": group_id,
            "user_exists": True,
            "created": False,
        }
    new_user = _create_user_sync(normalized, firstname, lastname)
    _add_to_group_sync(new_user["id"], group_id)
    return {
        "email": normalized,
        "metabase_user_id": new_user["id"],
        "metabase_group_id": group_id,
        "user_exists": False,
        "created": True,
    }


# ── Async public interface ────────────────────────────────────────────────────

async def list_groups() -> list:
    return await asyncio.to_thread(_list_groups_sync)


async def get_group_by_name(name: str) -> Optional[dict]:
    """Return the Metabase group matching the given name, or None."""
    return await asyncio.to_thread(_get_group_by_name_sync, name)


async def create_group(name: str) -> dict:
    """
    Create a new Metabase permission group.
    Raises RuntimeError with prefix 'DUPLICATE_GROUP:<id>:<name>' if one already exists.
    """
    return await asyncio.to_thread(_create_group_sync, name)


async def provision_user(email: str, firstname: str, lastname: str, group_id: int) -> dict:
    return await asyncio.to_thread(_provision_user_sync, email, firstname, lastname, group_id)


async def remove_from_group(mb_user_id: int, group_id: int) -> bool:
    return await asyncio.to_thread(_remove_from_group_sync, mb_user_id, group_id)


async def get_user_memberships(mb_user_id: int) -> list:
    return await asyncio.to_thread(_get_user_memberships_sync, mb_user_id)
