"""
Jira integration via Atlassian REST API v3.

One organisation → one Jira project (type: business / company-managed).
Board URL : {base_url}/jira/core/projects/{KEY}/board

Naming   : "{client_name} x Hypatos"
Key rules : 2–7 uppercase letters, not reserved, not already in Jira
Schemes assigned on creation (same IDs as existing Hypatos projects):
    Workflow scheme          10145
    Issue type scheme        10466
    Issue type screen scheme 10137
    Permission scheme        10087
Default groups added to Admin role (10002) on creation:
    COE, administrators

Auth: HTTP Basic  → base64(email:api_token)
"""

import asyncio
import base64
import logging
from typing import Optional

import httpx

from app.config import integration_settings

logger = logging.getLogger(__name__)

_BASE_V3 = "https://hypatos.atlassian.net/rest/api/3"
_BASE_V2 = "https://hypatos.atlassian.net/rest/api/2"
_TIMEOUT  = 30

# ── Hardcoded Jira constants (from existing app) ──────────────────────────────

LEAD_USER_MAPPING: dict[str, str] = {
    "elena.kuhn":         "712020:9de34ad3-f71e-4093-bd04-354b08b4a982",
    "jorge.costa":        "621d1acfb7e7c700715583e7",
    "stephan.kuche":      "630cd2ab3310c2492b59c51f",
    "yavuz.guney":        "712020:37b7fd3e-db24-433f-88d7-e84bb8d27551",
    "olga.milcent":       "712020:fdca536f-f91c-4d77-aebd-bbdd02825291",
    "andre.borzzatto":    "712020:886a6920-6c34-49c2-aa07-af749853588b",
    "ekaterina.mironova": "712020:45df7004-d0c2-4759-a3d6-c5737d5be307",
}

EXCLUDED_KEYS = {
    "CSLP","CSNEW","EM","ZZZ","SIM","BXIMH","DFM","SE","ROP","OKR",
    "FIPR","REQMAN","MBZ","T3S","SKK","PMO","TESTC","DUR","PS","PE",
    "TESTB","KATE","MDG","TESTA","UGI","TESTD","TOH","MON","DBFM",
    "ND2NDSLTNM","FINCS",
}

_PROJECT_TEMPLATE    = "com.atlassian.jira-core-project-templates:jira-core-simplified-project-management"
_ADMIN_ROLE_ID       = "10002"
_EXTERNAL_ROLE_ID    = "10224"
_DEFAULT_GROUPS      = ["COE", "administrators"]
_WORKFLOW_SCHEME_ID  = "10145"
_IT_SCHEME_ID        = "10466"
_ITS_SCREEN_SCHEME_ID= "10137"
_PERMISSION_SCHEME_ID= "10087"


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _check_config() -> None:
    cfg = integration_settings
    missing = [k for k, v in [
        ("JIRA_EMAIL",     cfg.JIRA_EMAIL),
        ("JIRA_API_TOKEN", cfg.JIRA_API_TOKEN),
    ] if not v]
    if missing:
        raise RuntimeError(f"Jira not configured — missing: {', '.join(missing)}")


def _headers() -> dict:
    cfg = integration_settings
    token = base64.b64encode(
        f"{cfg.JIRA_EMAIL}:{cfg.JIRA_API_TOKEN}".encode()
    ).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }


def _get(url: str, params: dict | None = None) -> dict:
    resp = httpx.get(url, headers=_headers(), params=params or {}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _post(url: str, payload: dict, success_codes=(200, 201)) -> dict:
    resp = httpx.post(url, headers=_headers(), json=payload, timeout=_TIMEOUT)
    if resp.status_code not in success_codes:
        try:
            err = resp.json()
            detail = err.get("errorMessages") or err.get("errors") or resp.text[:400]
        except Exception:
            detail = resp.text[:400]
        raise RuntimeError(f"Jira POST {url} → {resp.status_code}: {detail}")
    return resp.json() if resp.content else {}


def _put(url: str, payload: dict, success_codes=(200, 204)) -> dict:
    resp = httpx.put(url, headers=_headers(), json=payload, timeout=_TIMEOUT)
    if resp.status_code not in success_codes:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text[:400]
        raise RuntimeError(f"Jira PUT {url} → {resp.status_code}: {detail}")
    return resp.json() if resp.content else {}


def _delete(url: str, success_codes=(200, 204)) -> bool:
    resp = httpx.delete(url, headers=_headers(), timeout=_TIMEOUT)
    if resp.status_code == 404:
        return False
    if resp.status_code not in success_codes:
        raise RuntimeError(f"Jira DELETE {url} → {resp.status_code}")
    return True


# ── Key / name validation ─────────────────────────────────────────────────────

def validate_key(key: str) -> str:
    """
    Returns an error message string, or '' if the key is valid.
    Key rules:
      - 2–7 uppercase letters (A-Z only, no digits or symbols)
      - not in reserved EXCLUDED_KEYS set
    (Uniqueness against Jira is checked separately via the API.)
    """
    k = key.strip().upper()
    if not k:
        return "Project key is required"
    if not 2 <= len(k) <= 7:
        return "Project key must be 2–7 characters"
    if not k.isalpha():
        return "Project key must contain only letters A–Z"
    if k in EXCLUDED_KEYS:
        return f"Key '{k}' is reserved and cannot be used"
    return ""


def project_name_from_org(org_name: str) -> str:
    """Applies the standard naming convention: '{name} x Hypatos'"""
    return f"{org_name.strip()} x Hypatos"


def board_url(project_key: str) -> str:
    return f"https://hypatos.atlassian.net/jira/core/projects/{project_key}/board"


# ── API — project lookup ──────────────────────────────────────────────────────

def _get_project_sync(project_key: str) -> Optional[dict]:
    _check_config()
    resp = httpx.get(
        f"{_BASE_V3}/project/{project_key.upper()}",
        headers=_headers(), timeout=_TIMEOUT,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _project_name_exists_sync(name: str) -> bool:
    """True if any project with this exact name already exists in the workspace."""
    _check_config()
    start = 0
    while True:
        data = _get(f"{_BASE_V3}/project/search", {
            "startAt": start, "maxResults": 50, "orderBy": "name",
        })
        for p in data.get("values", []):
            if (p.get("name") or "").lower() == name.lower():
                return True
        if data.get("isLast", True) or len(data.get("values", [])) < 50:
            break
        start += 50
    return False


def _list_projects_sync() -> list:
    _check_config()
    projects, start = [], 0
    while True:
        data = _get(f"{_BASE_V3}/project/search", {
            "typeKey": "business", "startAt": start,
            "maxResults": 50, "orderBy": "name",
        })
        for p in data.get("values", []):
            projects.append({
                "id":        p.get("id"),
                "key":       p.get("key"),
                "name":      p.get("name"),
                "board_url": board_url(p.get("key", "")),
            })
        if data.get("isLast", True) or len(data.get("values", [])) < 50:
            break
        start += 50
    return projects


# ── API — scheme assignments ──────────────────────────────────────────────────

def _assign_workflow_scheme_sync(project_id: str) -> None:
    logger.info("Jira: assigning workflow scheme to project %s", project_id)
    # 202 = Jira accepted an async migration task (expected for existing issues)
    # 204 = applied immediately (expected for brand-new projects)
    _put(f"{_BASE_V3}/workflowscheme/project", {
        "projectId": project_id,
        "workflowSchemeId": _WORKFLOW_SCHEME_ID,
    }, success_codes=(200, 202, 204))
    logger.info("Jira: workflow scheme assigned")


def _assign_issue_type_scheme_sync(project_id: str) -> None:
    logger.info("Jira: assigning issue type scheme to project %s", project_id)
    _put(f"{_BASE_V3}/issuetypescheme/project", {
        "issueTypeSchemeId": _IT_SCHEME_ID,
        "projectId": project_id,
    })
    logger.info("Jira: issue type scheme assigned")


def _assign_issue_type_screen_scheme_sync(project_id: str) -> None:
    logger.info("Jira: assigning issue type screen scheme to project %s", project_id)
    _put(f"{_BASE_V3}/issuetypescreenscheme/project", {
        "issueTypeScreenSchemeId": _ITS_SCREEN_SCHEME_ID,
        "projectId": project_id,
    })
    logger.info("Jira: issue type screen scheme assigned")


def _assign_permission_scheme_sync(project_id: str) -> None:
    logger.info("Jira: assigning permission scheme to project %s", project_id)
    _put(f"{_BASE_V3}/project/{project_id}/permissionscheme", {
        "id": int(_PERMISSION_SCHEME_ID),
    })
    logger.info("Jira: permission scheme assigned")


def _assign_default_groups_sync(project_key: str) -> None:
    """Assign COE + administrators groups to the Admin role."""
    logger.info("Jira: assigning default groups to project %s", project_key)
    _post(
        f"{_BASE_V3}/project/{project_key}/role/{_ADMIN_ROLE_ID}",
        {"group": _DEFAULT_GROUPS},
    )
    logger.info("Jira: default groups assigned")


# ── API — project creation (full flow) ───────────────────────────────────────

def _create_project_sync(
    client_name: str,
    key: str,
    lead_account_id: str,
) -> dict:
    """
    Full project-creation pipeline matching the existing Hypatos Jira app:
      1. Validate key format (2–7 alpha, not excluded)
      2. Check key not already in Jira
      3. Build name '{client_name} x Hypatos' and check name uniqueness
      4. Create project via API v2  ← v2 is used because it reliably honours
         the caller-supplied key; v3 has been observed to auto-generate keys
      5. Assign workflow scheme        (10145)
      6. Assign issue type screen scheme (10137)
      7. Assign issue type scheme      (10466)
      8. Assign permission scheme      (10087)
      9. Assign default groups to Admin role (COE, administrators → 10002)

    Returns {id, key, name, board_url}.
    Raises ValueError for validation/conflict errors, RuntimeError for API errors.
    """
    import time

    _check_config()
    key = key.strip().upper()

    # 1. Key format
    err = validate_key(key)
    if err:
        raise ValueError(err)

    # 2. Key uniqueness
    if _get_project_sync(key) is not None:
        raise ValueError(f"Project key '{key}' already exists in Jira")

    # 3. Build name + check uniqueness
    name = project_name_from_org(client_name)
    if _project_name_exists_sync(name):
        raise ValueError(
            f"A project named '{name}' already exists in Jira. "
            "Choose a different client name."
        )

    logger.info(
        "Jira: creating project key=%s name='%s' lead_account_id=%s",
        key, name, lead_account_id,
    )

    # 4. Create project (v2 endpoint — honours the supplied key reliably)
    data = _post(f"{_BASE_V2}/project", {
        "key":               key,
        "name":              name,
        "projectTypeKey":    "business",
        "projectTemplateKey":_PROJECT_TEMPLATE,
        "leadAccountId":     lead_account_id,
        "assigneeType":      "UNASSIGNED",
    }, success_codes=(200, 201))

    project_id  = str(data["id"])
    project_key = data["key"]
    logger.info("Jira: project created id=%s key=%s", project_id, project_key)

    # Brief pause — lets Jira finish internal project initialisation before
    # we start assigning schemes (avoids sporadic 404s on brand-new projects)
    time.sleep(2)

    # 5-8. Assign schemes (all via v3 endpoints)
    _assign_workflow_scheme_sync(project_id)
    _assign_issue_type_screen_scheme_sync(project_id)
    _assign_issue_type_scheme_sync(project_id)
    _assign_permission_scheme_sync(project_id)

    # 9. Assign default groups to Admin role
    _assign_default_groups_sync(project_key)

    return {
        "id":        project_id,
        "key":       project_key,
        "name":      name,
        "board_url": board_url(project_key),
    }


def _delete_project_sync(project_key: str) -> bool:
    _check_config()
    return _delete(f"{_BASE_V3}/project/{project_key.upper()}")


# ── Async public interface ────────────────────────────────────────────────────

async def create_project(client_name: str, key: str, lead_account_id: str) -> dict:
    return await asyncio.to_thread(_create_project_sync, client_name, key, lead_account_id)


async def get_project(project_key: str) -> Optional[dict]:
    return await asyncio.to_thread(_get_project_sync, project_key)


async def list_projects() -> list:
    return await asyncio.to_thread(_list_projects_sync)


async def delete_project(project_key: str) -> bool:
    return await asyncio.to_thread(_delete_project_sync, project_key)
