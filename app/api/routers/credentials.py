"""
Admin Credentials page endpoints.

GET  /credentials/          → all integration credential groups (secrets masked)
PUT  /credentials/          → upsert provided values; live-overlay onto settings
POST /credentials/test/{group_id} → lightweight connectivity check for a group

Values are stored in the `integration_credential` table and overlaid onto the
in-memory `integration_settings` object so adapters keep working unchanged.
SMTP is managed via the separate /smtp-config/ endpoints.
"""

import base64
import asyncio
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database.session import SessionDep
from app.database.models import IntegrationCredential
from app.config import integration_settings
from app.credentials_store import CREDENTIAL_GROUPS, ALL_FIELDS, apply_to_settings

router = APIRouter(prefix="/credentials", tags=["Credentials"])

_TIMEOUT = 15


# ── Schemas ───────────────────────────────────────────────────────────────────

class CredentialUpdate(BaseModel):
    values: dict[str, Optional[str]]


# ── Read ────────────────────────────────────────────────────────────────────

@router.get("/")
async def get_credentials(session: SessionDep):
    rows = (await session.execute(select(IntegrationCredential))).scalars().all()
    db_map = {r.key: r.value for r in rows}

    groups = []
    for g in CREDENTIAL_GROUPS:
        fields = []
        for f in g.fields:
            db_val = db_map.get(f.key)
            env_val = getattr(integration_settings, f.key, None)
            has_db = db_val not in (None, "")
            effective = db_val if has_db else env_val
            is_set = bool(effective)
            source = "db" if has_db else ("env" if env_val else "none")
            fields.append({
                "key": f.key,
                "label": f.label,
                "secret": f.secret,
                "placeholder": f.placeholder,
                "help": f.help,
                "is_set": is_set,
                "source": source,
                # Never expose secret values; non-secrets are returned for editing.
                "value": "" if f.secret else (effective or ""),
            })
        groups.append({"id": g.id, "name": g.name, "icon": g.icon, "fields": fields})
    return {"groups": groups}


# ── Write ─────────────────────────────────────────────────────────────────────

@router.put("/")
async def update_credentials(body: CredentialUpdate, session: SessionDep):
    updated: list[str] = []
    for key, value in body.values.items():
        f = ALL_FIELDS.get(key)
        if f is None:
            continue
        # For secrets, an empty value means "leave unchanged".
        if f.secret and (value is None or value == ""):
            continue

        row = await session.get(IntegrationCredential, key)
        if row is None:
            row = IntegrationCredential(key=key, value=value or "")
            session.add(row)
        else:
            row.value = value or ""
            row.updated_at = datetime.utcnow()

        apply_to_settings(key, value)   # live overlay so adapters see it immediately
        updated.append(key)

    await session.commit()
    return {"ok": True, "updated": updated}


# ── Connectivity tests ────────────────────────────────────────────────────────

def _test_metabase_sync() -> str:
    base = (integration_settings.METABASE_URL or "").rstrip("/")
    key = integration_settings.METABASE_API_KEY
    if not base or not key:
        raise RuntimeError("METABASE_URL and METABASE_API_KEY are required")
    r = httpx.get(f"{base}/api/user/current",
                  headers={"x-api-key": key}, timeout=_TIMEOUT)
    r.raise_for_status()
    u = r.json()
    return f"Connected as {u.get('common_name') or u.get('email') or 'user'}"


def _test_slack_sync() -> str:
    token = integration_settings.SLACK_BOT_TOKEN
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN is required")
    r = httpx.get("https://slack.com/api/auth.test",
                  headers={"Authorization": f"Bearer {token}"}, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack error: {data.get('error', 'unknown')}")
    return f"Connected to {data.get('team')} as {data.get('user')}"


def _test_jira_sync() -> str:
    cfg = integration_settings
    if not cfg.JIRA_BASE_URL or not cfg.JIRA_EMAIL or not cfg.JIRA_API_TOKEN:
        raise RuntimeError("JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN are required")
    token = base64.b64encode(f"{cfg.JIRA_EMAIL}:{cfg.JIRA_API_TOKEN}".encode()).decode()
    r = httpx.get(f"{cfg.JIRA_BASE_URL.rstrip('/')}/rest/api/3/myself",
                  headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
                  timeout=_TIMEOUT)
    r.raise_for_status()
    u = r.json()
    return f"Connected as {u.get('displayName') or u.get('emailAddress') or 'user'}"


def _test_azure_sync() -> str:
    cfg = integration_settings
    if not cfg.AZURE_TENANT_ID or not cfg.AZURE_CLIENT_ID or not cfg.AZURE_CLIENT_SECRET:
        raise RuntimeError("AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET are required")
    r = httpx.post(
        f"https://login.microsoftonline.com/{cfg.AZURE_TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type": "client_credentials",
            "client_id": cfg.AZURE_CLIENT_ID,
            "client_secret": cfg.AZURE_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
        }, timeout=_TIMEOUT)
    r.raise_for_status()
    if not r.json().get("access_token"):
        raise RuntimeError("No access token returned")
    return "Acquired access token successfully"


# Sync tests run in a thread; async tests (adapters) are awaited directly.
_SYNC_TESTS = {
    "metabase": _test_metabase_sync,
    "slack": _test_slack_sync,
    "jira": _test_jira_sync,
    "azure": _test_azure_sync,
}


async def _test_salesforce():
    from app.adapters import salesforce
    return await salesforce.test_connection()


# Studio is tested per-cluster via /studio-clusters/{id}/test (multiple clusters).
_ASYNC_TESTS = {
    "salesforce": _test_salesforce,
}


@router.post("/test/{group_id}")
async def test_credentials(group_id: str):
    try:
        if group_id in _ASYNC_TESTS:
            message = await _ASYNC_TESTS[group_id]()
        elif group_id in _SYNC_TESTS:
            message = await asyncio.to_thread(_SYNC_TESTS[group_id])
        else:
            raise HTTPException(status_code=404, detail=f"No connectivity test for '{group_id}'")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection failed: {str(e)}")
    return {"ok": True, "message": message}
