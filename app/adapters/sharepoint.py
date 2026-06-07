"""
SharePoint integration via Microsoft Graph API.

Copies the folder structure from the CS-Templates SharePoint site into the
SharePoint site that is automatically associated with each org's Teams team.

Required Azure AD app permissions (Application — admin consent):
    Sites.ReadWrite.All   read template site + write to any org SharePoint

Same Azure AD credentials as Teams (AZURE_TENANT_ID / CLIENT_ID / CLIENT_SECRET).

Template site : https://hypatos.sharepoint.com/sites/CSTemplates
Template team : 79fd3ef7-bb78-47ba-b115-c190842b6030  (owner of above site)
FolderCTID    : 0x012000AC790AB4AFD41A4BACEE84854022D3D1
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

from app.config import integration_settings

_BASE = "https://graph.microsoft.com/v1.0"
_TIMEOUT = 30

logger = logging.getLogger(__name__)

# ── Template constants ────────────────────────────────────────────────────────
_TEMPLATE_HOSTNAME    = "hypatos.sharepoint.com"
_TEMPLATE_SITE_PATH   = "/sites/CSTemplates"
_TEMPLATE_SITE_URL    = f"https://{_TEMPLATE_HOSTNAME}{_TEMPLATE_SITE_PATH}"
_TEMPLATE_FOLDER_CTID = "0x012000AC790AB4AFD41A4BACEE84854022D3D1"

# The specific "Project" folder to copy (Freigegebene Dokumente/Project)
_TEMPLATE_FOLDER_ID   = "01BFQU2H26EYJ5I3JKERDYUEZFZJITPFIR"
_TEMPLATE_FOLDER_NAME = "Project"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_config() -> None:
    cfg = integration_settings
    missing = [
        name for name, val in [
            ("AZURE_TENANT_ID",    cfg.AZURE_TENANT_ID),
            ("AZURE_CLIENT_ID",    cfg.AZURE_CLIENT_ID),
            ("AZURE_CLIENT_SECRET", cfg.AZURE_CLIENT_SECRET),
        ] if not val
    ]
    if missing:
        raise RuntimeError(
            f"SharePoint integration not configured. Missing: {', '.join(missing)}"
        )


def _get_token_sync() -> str:
    _check_config()
    cfg = integration_settings
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


# ── Site + drive helpers ──────────────────────────────────────────────────────

def _get_site_by_url_sync(hostname: str, site_path: str, token: str) -> dict:
    """GET /sites/{hostname}:{site_path}"""
    url = f"{_BASE}/sites/{hostname}:{site_path}"
    resp = httpx.get(url, headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _get_site_drive_sync(site_id: str, token: str) -> dict:
    """GET /sites/{site_id}/drive — default document library."""
    resp = httpx.get(f"{_BASE}/sites/{site_id}/drive", headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _get_group_site_sync(group_id: str, token: str) -> dict:
    """GET /groups/{group_id}/sites/root — the SharePoint site for a Teams group."""
    resp = httpx.get(f"{_BASE}/groups/{group_id}/sites/root", headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _get_drive_root_sync(drive_id: str, token: str) -> dict:
    """GET /drives/{drive_id}/root — root folder item."""
    resp = httpx.get(f"{_BASE}/drives/{drive_id}/root", headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _list_drive_root_children_sync(drive_id: str, token: str) -> list:
    """GET /drives/{drive_id}/root/children — list top-level items."""
    resp = httpx.get(f"{_BASE}/drives/{drive_id}/root/children", headers=_h(token), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("value", [])


# ── Copy ──────────────────────────────────────────────────────────────────────

def _copy_item_sync(
    src_drive_id: str,
    src_item_id: str,
    dest_drive_id: str,
    dest_item_id: str,
    name: str,
    token: str,
) -> dict:
    """
    POST /drives/{src_drive_id}/items/{src_item_id}/copy
    Async Graph operation — returns 202 with a Location (monitor) URL.
    Returns {name, status, monitor_url}.
    """
    payload = {
        "parentReference": {
            "driveId": dest_drive_id,
            "id":      dest_item_id,
        },
        "name": name,
    }
    resp = httpx.post(
        f"{_BASE}/drives/{src_drive_id}/items/{src_item_id}/copy",
        headers={**_h(token), "Prefer": "respond-async"},
        json=payload,
        timeout=_TIMEOUT,
        follow_redirects=False,
    )

    if resp.status_code == 202:
        monitor_url = resp.headers.get("Location", "")
        logger.info("SharePoint: copy started for '%s' — monitor: %s", name, monitor_url[:80])
        return {"name": name, "status": "started", "monitor_url": monitor_url}

    if resp.status_code in (200, 201):
        logger.info("SharePoint: copy of '%s' completed synchronously", name)
        return {"name": name, "status": "completed", "monitor_url": ""}

    resp.raise_for_status()
    return {"name": name, "status": "unknown"}


def _poll_copy_sync(monitor_url: str, max_wait: int = 15) -> str:
    """
    Poll a copy monitor URL until completion or timeout.
    Returns the final status string: "completed" | "failed" | "inProgress".
    """
    if not monitor_url:
        return "completed"
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        try:
            r = httpx.get(monitor_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                status = data.get("status", "")
                if status == "completed":
                    return "completed"
                if status == "failed":
                    logger.error("SharePoint copy failed: %s", data)
                    return "failed"
        except Exception as exc:
            logger.warning("SharePoint poll error: %s", exc)
        time.sleep(2)
    return "inProgress"


# ── Main compound operation ───────────────────────────────────────────────────

def _copy_template_to_org_sync(group_id: str) -> dict:
    """
    Copy the 'Project' template folder (and all its children) from CSTemplates
    into the root of the org's Teams-linked SharePoint document library.

    Source item : drives/{template_drive}/items/01BFQU2HYCXP2O2OXVKVAZ73I6E42F2QUS
    Dest        : root of the org team's default document library
    """
    token = _get_token_sync()

    # ── 1. Template site & drive ──────────────────────────────────────────────
    logger.info("SharePoint: fetching template site %s", _TEMPLATE_SITE_URL)
    template_site  = _get_site_by_url_sync(_TEMPLATE_HOSTNAME, _TEMPLATE_SITE_PATH, token)
    template_drive = _get_site_drive_sync(template_site["id"], token)
    logger.info("SharePoint: template drive id=%s", template_drive["id"])

    # ── 2. Org Teams site & drive ─────────────────────────────────────────────
    logger.info("SharePoint: fetching org site for group %s", group_id)
    org_site  = _get_group_site_sync(group_id, token)
    org_drive = _get_site_drive_sync(org_site["id"], token)
    org_root  = _get_drive_root_sync(org_drive["id"], token)
    logger.info("SharePoint: org drive id=%s  root item id=%s", org_drive["id"], org_root["id"])

    # ── 3. Copy the single template folder (with all children) ───────────────
    logger.info(
        "SharePoint: copying folder '%s' (id=%s) → org root",
        _TEMPLATE_FOLDER_NAME, _TEMPLATE_FOLDER_ID,
    )
    try:
        op = _copy_item_sync(
            src_drive_id  = template_drive["id"],
            src_item_id   = _TEMPLATE_FOLDER_ID,
            dest_drive_id = org_drive["id"],
            dest_item_id  = org_root["id"],
            name          = _TEMPLATE_FOLDER_NAME,
            token         = token,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        detail      = exc.response.text[:300]
        logger.error("SharePoint: copy failed (%d): %s", status_code, detail)
        op = {"name": _TEMPLATE_FOLDER_NAME, "status": "error", "detail": detail}

    # ── 4. Poll until completed (or timeout) ─────────────────────────────────
    if op.get("status") == "started" and op.get("monitor_url"):
        op["status"] = _poll_copy_sync(op["monitor_url"], max_wait=20)

    return {
        "template_site_url":  template_site.get("webUrl", _TEMPLATE_SITE_URL),
        "org_site_url":       org_site.get("webUrl", ""),
        "folder_name":        _TEMPLATE_FOLDER_NAME,
        "status":             op["status"],
        "operations":         [op],
    }


# ── Async public interface ────────────────────────────────────────────────────

async def copy_template_to_org(group_id: str) -> dict:
    return await asyncio.to_thread(_copy_template_to_org_sync, group_id)
