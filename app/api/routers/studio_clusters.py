"""
Hypatos Studio cluster credentials — CRUD + connectivity test.

Studio runs on multiple clusters (e.g. EU / US), each with its own OAuth
client-credentials pair. Managed on the Credentials page.

GET    /studio-clusters/            → list (client_secret masked)
POST   /studio-clusters/            → create
PATCH  /studio-clusters/{id}        → update (blank client_secret keeps existing)
DELETE /studio-clusters/{id}        → delete
POST   /studio-clusters/{id}/test   → acquire a token to verify credentials
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database.session import SessionDep
from app.database.models import StudioCluster
from app.adapters import studio
from app.adapters.studio import StudioCreds

router = APIRouter(prefix="/studio-clusters", tags=["Studio Clusters"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ClusterCreate(BaseModel):
    name: str
    base_url: str
    client_id: str
    client_secret: str
    is_default: bool = False


class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None   # blank/None = keep existing
    is_default: Optional[bool] = None


def _to_read(c: StudioCluster) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "base_url": c.base_url,
        "client_id": c.client_id,
        "client_secret_set": bool(c.client_secret),
        "is_default": c.is_default,
        "updated_at": c.updated_at,
    }


async def _clear_other_defaults(session, keep_id: Optional[UUID]) -> None:
    rows = (await session.execute(select(StudioCluster).where(StudioCluster.is_default == True))).scalars().all()
    for r in rows:
        if r.id != keep_id:
            r.is_default = False


async def resolve_cluster_creds(
    session,
    *,
    cluster_id: Optional[UUID] = None,
    name: Optional[str] = None,
    fall_back_to_default: bool = True,
) -> StudioCreds:
    """Resolve a Studio cluster to its credentials for use by integration actions.

    Pass `cluster_id` or `name` to pick a specific cluster ("one or the other").
    If neither is given and `fall_back_to_default` is True, the default cluster is
    used. Raises 404 if the requested cluster (or any default) can't be found.

    Future Studio action endpoints should call this, then hand the result to
    `app.adapters.studio.request(creds, ...)`.
    """
    cluster: Optional[StudioCluster] = None
    if cluster_id is not None:
        cluster = await session.get(StudioCluster, cluster_id)
    elif name is not None:
        cluster = (
            await session.execute(select(StudioCluster).where(StudioCluster.name == name))
        ).scalars().first()
    elif fall_back_to_default:
        cluster = (
            await session.execute(select(StudioCluster).where(StudioCluster.is_default == True))
        ).scalars().first()

    if cluster is None:
        raise HTTPException(status_code=404, detail="Studio cluster not found")

    return StudioCreds(
        base_url=cluster.base_url,
        client_id=cluster.client_id,
        client_secret=cluster.client_secret,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
async def list_clusters(session: SessionDep):
    rows = (await session.execute(select(StudioCluster).order_by(StudioCluster.name))).scalars().all()
    return [_to_read(c) for c in rows]


@router.post("/")
async def create_cluster(body: ClusterCreate, session: SessionDep):
    existing = (await session.execute(select(StudioCluster))).scalars().all()
    c = StudioCluster(
        name=body.name, base_url=body.base_url,
        client_id=body.client_id, client_secret=body.client_secret,
        # first cluster created becomes the default automatically
        is_default=body.is_default or len(existing) == 0,
    )
    session.add(c)
    await session.flush()   # assigns c.id so we can exclude it when clearing other defaults
    if c.is_default:
        await _clear_other_defaults(session, keep_id=c.id)
    await session.commit()
    await session.refresh(c)
    return _to_read(c)


@router.patch("/{cluster_id}")
async def update_cluster(cluster_id: UUID, body: ClusterUpdate, session: SessionDep):
    c = await session.get(StudioCluster, cluster_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cluster not found")
    data = body.model_dump(exclude_none=True)
    # An empty client_secret means "keep existing".
    if not data.get("client_secret"):
        data.pop("client_secret", None)
    for k, v in data.items():
        setattr(c, k, v)
    c.updated_at = datetime.utcnow()
    if data.get("is_default"):
        await _clear_other_defaults(session, keep_id=c.id)
    await session.commit()
    await session.refresh(c)
    return _to_read(c)


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: UUID, session: SessionDep):
    c = await session.get(StudioCluster, cluster_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cluster not found")
    was_default = c.is_default
    await session.delete(c)
    await session.commit()
    # if we removed the default, promote the first remaining cluster
    if was_default:
        remaining = (await session.execute(select(StudioCluster).order_by(StudioCluster.name))).scalars().first()
        if remaining:
            remaining.is_default = True
            await session.commit()
    return {"ok": True}


@router.post("/{cluster_id}/test")
async def test_cluster(cluster_id: UUID, session: SessionDep):
    c = await session.get(StudioCluster, cluster_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cluster not found")
    creds = StudioCreds(base_url=c.base_url, client_id=c.client_id, client_secret=c.client_secret)
    try:
        message = await studio.test_connection(creds)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connection failed: {str(e)}")
    return {"ok": True, "message": message}
