"""
Hypatos Studio adapter.

Studio runs on multiple clusters (e.g. EU / US), each with its own OAuth
client-credentials pair. Cluster credentials are stored in the `studio_cluster`
table and managed on the Credentials page. The caller resolves which cluster to
use and passes its credentials in, so this adapter stays free of DB access and
remains a pure, sync-friendly HTTP layer.

This is a scaffold: token acquisition + a generic `request()` helper. Add typed
create/read/update/delete wrappers once the specific endpoints are known, and
adjust `_TOKEN_PATH` to the real token endpoint.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 20
# Adjust to the real token endpoint once confirmed.
_TOKEN_PATH = "/oauth/token"


@dataclass
class StudioCreds:
    base_url: str
    client_id: str
    client_secret: str

    def base(self) -> str:
        return self.base_url.rstrip("/")


# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_token_sync(creds: StudioCreds) -> str:
    if not creds.base_url or not creds.client_id or not creds.client_secret:
        raise RuntimeError("Studio cluster is missing base URL, client ID or client secret")
    resp = httpx.post(
        f"{creds.base()}{_TOKEN_PATH}",
        data={
            "grant_type": "client_credentials",
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── Generic request helper (sync; wrapped at call site) ───────────────────────

def _request_sync(creds: StudioCreds, method: str, path: str, *,
                  params: Optional[dict] = None, json: Optional[Any] = None) -> Any:
    token = _get_token_sync(creds)
    url = f"{creds.base()}/{path.lstrip('/')}"
    resp = httpx.request(method.upper(), url, headers=_headers(token),
                         params=params, json=json, timeout=_TIMEOUT)
    resp.raise_for_status()
    if resp.headers.get("content-type", "").startswith("application/json"):
        return resp.json()
    return resp.text


# ── Public async API ──────────────────────────────────────────────────────────

async def request(creds: StudioCreds, method: str, path: str, *,
                  params: Optional[dict] = None, json: Optional[Any] = None) -> Any:
    """Authenticated request against a Studio cluster. Use this until typed
    create/read/update/delete wrappers are added."""
    return await asyncio.to_thread(_request_sync, creds, method, path, params=params, json=json)


async def test_connection(creds: StudioCreds) -> str:
    """Acquire a token to verify a cluster's credentials."""
    await asyncio.to_thread(_get_token_sync, creds)
    return "Acquired Studio access token successfully"
