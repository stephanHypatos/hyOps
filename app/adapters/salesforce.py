"""
Salesforce adapter — read data from a Salesforce instance.

Auth: OAuth 2.0 against a Connected App. Two flows are supported automatically:
  • username-password flow  — used when SALESFORCE_USERNAME is set
  • client-credentials flow — used otherwise

Credentials are configured on the admin Credentials page and read from
`integration_settings` (DB overlays .env). Sync httpx calls are wrapped with
`asyncio.to_thread` at the call site, matching the other adapters.

NOTE: the read actions here (SOQL query + get account) are a starting point that
matches the stated use case ("read data from a specific account"). Extend with
more endpoints as the requirements firm up.
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.config import integration_settings

logger = logging.getLogger(__name__)

_TIMEOUT = 20
_API_VERSION = "v60.0"


# ── Config / auth ─────────────────────────────────────────────────────────────

def _check_config() -> None:
    cfg = integration_settings
    missing = [name for name, val in [
        ("SALESFORCE_INSTANCE_URL", cfg.SALESFORCE_INSTANCE_URL),
        ("SALESFORCE_CLIENT_ID", cfg.SALESFORCE_CLIENT_ID),
        ("SALESFORCE_CLIENT_SECRET", cfg.SALESFORCE_CLIENT_SECRET),
    ] if not val]
    if missing:
        raise RuntimeError(f"Salesforce not configured — missing: {', '.join(missing)}")


def _get_token_sync() -> tuple[str, str]:
    """Return (access_token, instance_url). Chooses the OAuth flow based on
    whether a username is configured."""
    _check_config()
    cfg = integration_settings
    login_url = cfg.SALESFORCE_INSTANCE_URL.rstrip("/")
    token_url = f"{login_url}/services/oauth2/token"

    if cfg.SALESFORCE_USERNAME:
        data = {
            "grant_type": "password",
            "client_id": cfg.SALESFORCE_CLIENT_ID,
            "client_secret": cfg.SALESFORCE_CLIENT_SECRET,
            "username": cfg.SALESFORCE_USERNAME,
            "password": (cfg.SALESFORCE_PASSWORD or "") + (cfg.SALESFORCE_SECURITY_TOKEN or ""),
        }
    else:
        data = {
            "grant_type": "client_credentials",
            "client_id": cfg.SALESFORCE_CLIENT_ID,
            "client_secret": cfg.SALESFORCE_CLIENT_SECRET,
        }

    resp = httpx.post(token_url, data=data, timeout=_TIMEOUT)
    resp.raise_for_status()
    body = resp.json()
    # Salesforce returns the concrete instance host to use for subsequent calls.
    return body["access_token"], body.get("instance_url", login_url).rstrip("/")


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Read helpers (sync; wrapped at call site) ─────────────────────────────────

def _soql_query_sync(soql: str) -> dict:
    token, instance = _get_token_sync()
    resp = httpx.get(
        f"{instance}/services/data/{_API_VERSION}/query",
        headers=_headers(token), params={"q": soql}, timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _get_account_sync(account_id: str) -> dict:
    token, instance = _get_token_sync()
    resp = httpx.get(
        f"{instance}/services/data/{_API_VERSION}/sobjects/Account/{account_id}",
        headers=_headers(token), timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


# ── Public async API ──────────────────────────────────────────────────────────

async def soql_query(soql: str) -> dict:
    """Run a SOQL query and return the raw Salesforce response."""
    return await asyncio.to_thread(_soql_query_sync, soql)


async def get_account(account_id: str) -> dict:
    """Fetch a single Account record by its Salesforce Id."""
    return await asyncio.to_thread(_get_account_sync, account_id)


async def test_connection() -> str:
    """Acquire a token to verify the configured credentials."""
    _, instance = await asyncio.to_thread(_get_token_sync)
    return f"Connected to {instance}"
