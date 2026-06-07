"""
Jira integration endpoints.

Org-level:
    GET    /jira/organization/{org_id}/project         — get linked project
    POST   /jira/organization/{org_id}/create-project  — create new + store
    PUT    /jira/organization/{org_id}/project         — link existing by key
    DELETE /jira/organization/{org_id}/project         — unlink (DB only)

Lead-user management:
    GET    /jira/lead-users             — list all configured lead users
    POST   /jira/lead-users             — add a new lead user
    DELETE /jira/lead-users/{user_id}   — remove a lead user

Admin:
    GET    /jira/projects               — list all business projects in workspace
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.adapters import jira as jira_adapter
from app.database.models import JiraLeadUser, Organization, OrganizationJiraProject
from app.database.session import SessionDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jira", tags=["Jira Integration"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateJiraProjectBody(BaseModel):
    project_key: str        # 2–7 uppercase letters; validated by adapter
    lead_user_id: str       # UUID (pk of JiraLeadUser row)


class JiraProjectLink(BaseModel):
    project_key: str        # e.g. "FNK"
    project_name: str = ""  # optional override; Jira's name used if blank


class AddLeadUserBody(BaseModel):
    username: str           # e.g. "stephan.kuche"
    jira_account_id: str    # Atlassian account ID


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_linked_project(org_id: UUID, session: SessionDep):
    result = await session.execute(
        select(OrganizationJiraProject).where(
            OrganizationJiraProject.organization_id == org_id
        )
    )
    return result.scalars().first()


# ── Org-level ─────────────────────────────────────────────────────────────────

@router.get("/organization/{org_id}/project")
async def get_jira_project_for_org(org_id: UUID, session: SessionDep):
    proj = await _get_linked_project(org_id, session)
    if proj is None:
        raise HTTPException(status_code=404, detail="No Jira project configured for this organization")
    return {
        "id":           str(proj.id),
        "project_key":  proj.project_key,
        "project_id":   proj.project_id,
        "project_name": proj.project_name,
        "board_url":    proj.board_url,
    }


@router.post("/organization/{org_id}/create-project", status_code=200)
async def create_jira_project_for_org(
    org_id: UUID,
    body: CreateJiraProjectBody,
    session: SessionDep,
):
    """
    Create a new Jira business project for this organisation.

    - Project key    : provided by caller (2–7 uppercase letters)
    - Project name   : auto-set to '{org.name} x Hypatos'
    - Lead account   : looked up from jira_lead_user table by UUID
    - After creation : assigns 4 standard Hypatos schemes + default board groups

    Returns 409 if a project is already linked.
    Returns 422 for key / lead-user validation errors.
    Returns 502 for Jira API errors.
    """
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    if await _get_linked_project(org_id, session):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "A Jira project is already linked to this organization",
                "hint":    "Unlink first via DELETE, or change the link via PUT.",
            },
        )

    # Resolve lead user from DB
    try:
        lead_uuid = UUID(body.lead_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="lead_user_id must be a valid UUID")

    lead = await session.get(JiraLeadUser, lead_uuid)
    if lead is None:
        raise HTTPException(
            status_code=422,
            detail=f"Lead user '{body.lead_user_id}' not found — add them in Jira Settings first",
        )

    try:
        data = await jira_adapter.create_project(
            client_name=org.name,
            key=body.project_key,
            lead_account_id=lead.jira_account_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("Jira create-project error (org=%s): %s", org_id, exc, exc_info=True)
        raise HTTPException(status_code=502, detail=f"Jira API error: {exc}")

    session.add(OrganizationJiraProject(
        organization_id=org_id,
        project_key=data["key"],
        project_id=data["id"],
        project_name=data["name"],
        board_url=data["board_url"],
    ))
    await session.commit()

    return {
        "project_key":  data["key"],
        "project_id":   data["id"],
        "project_name": data["name"],
        "board_url":    data["board_url"],
        "created":      True,
    }


@router.put("/organization/{org_id}/project")
async def link_jira_project_for_org(
    org_id: UUID, body: JiraProjectLink, session: SessionDep
):
    """Link an *existing* Jira project to this organisation by key."""
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        remote = await jira_adapter.get_project(body.project_key.upper())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira error: {exc}")

    if remote is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project key '{body.project_key}' not found in Jira workspace",
        )

    existing = await _get_linked_project(org_id, session)
    key       = remote["key"]
    proj_name = body.project_name.strip() or remote.get("name", key)
    burl      = jira_adapter.board_url(key)

    if existing:
        existing.project_key  = key
        existing.project_id   = str(remote.get("id", ""))
        existing.project_name = proj_name
        existing.board_url    = burl
        session.add(existing)
    else:
        session.add(OrganizationJiraProject(
            organization_id=org_id,
            project_key=key,
            project_id=str(remote.get("id", "")),
            project_name=proj_name,
            board_url=burl,
        ))

    await session.commit()
    return {"project_key": key, "project_name": proj_name, "board_url": burl}


@router.delete("/organization/{org_id}/project")
async def unlink_jira_project_for_org(org_id: UUID, session: SessionDep):
    proj = await _get_linked_project(org_id, session)
    if proj is None:
        raise HTTPException(status_code=404, detail="No Jira project linked")
    await session.delete(proj)
    await session.commit()
    return {"detail": "Jira project unlinked"}


# ── Lead user management ──────────────────────────────────────────────────────

@router.get("/lead-users")
async def list_lead_users(session: SessionDep):
    """Return all configured Jira lead users (for the dropdown + admin panel)."""
    result = await session.execute(
        select(JiraLeadUser).order_by(JiraLeadUser.username)
    )
    users = result.scalars().all()
    return [
        {
            "id":              str(u.id),
            "username":        u.username,
            "jira_account_id": u.jira_account_id,
        }
        for u in users
    ]


@router.post("/lead-users", status_code=201)
async def add_lead_user(body: AddLeadUserBody, session: SessionDep):
    """Add a new lead user to the global list."""
    # Check for duplicates
    dup = await session.execute(
        select(JiraLeadUser).where(JiraLeadUser.username == body.username)
    )
    if dup.scalars().first():
        raise HTTPException(status_code=409, detail=f"Username '{body.username}' already exists")

    user = JiraLeadUser(
        username=body.username.strip().lower(),
        jira_account_id=body.jira_account_id.strip(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return {"id": str(user.id), "username": user.username, "jira_account_id": user.jira_account_id}


@router.delete("/lead-users/{user_id}", status_code=200)
async def delete_lead_user(user_id: UUID, session: SessionDep):
    """Remove a lead user from the global list."""
    user = await session.get(JiraLeadUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Lead user not found")
    await session.delete(user)
    await session.commit()
    return {"detail": f"Lead user '{user.username}' removed"}


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_all_jira_projects():
    """List all business projects in the Jira workspace (admin view)."""
    try:
        return await jira_adapter.list_projects()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Jira error: {exc}")
