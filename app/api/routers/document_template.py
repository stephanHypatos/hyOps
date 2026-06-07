import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database.models import (
    DocumentTemplate,
    DocumentationLink,
    User,
    OrganizationTeamsGroup,
    OrganizationSlackChannel,
    OrganizationJiraProject,
    OrganizationMetabaseGroup,
)
from app.database.session import SessionDep
from app.api.schemas.document_template import (
    DocumentTemplateCreate,
    DocumentTemplateRead,
    DocumentTemplateUpdate,
)

router = APIRouter(prefix="/document-template", tags=["Document Template"])


# ===================== Endpoints =====================

@router.get("/document-templates", response_model=list[DocumentTemplateRead])
async def get_all_document_templates(session: SessionDep):
    result = await session.execute(select(DocumentTemplate))
    return result.scalars().all()


@router.get("/", response_model=DocumentTemplateRead)
async def get_document_template(id: UUID, session: SessionDep):
    template = await session.get(DocumentTemplate, id)
    if not template:
        raise HTTPException(status_code=404, detail="Document Template not found")
    return template


@router.post("/", response_model=DocumentTemplateRead)
async def create_document_template(data: DocumentTemplateCreate, session: SessionDep):
    new_template = DocumentTemplate(**data.model_dump())
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    return new_template


@router.patch("/", response_model=DocumentTemplateRead)
async def update_document_template(id: UUID, data: DocumentTemplateUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    template = await session.get(DocumentTemplate, id)
    if not template:
        raise HTTPException(status_code=404, detail="Document Template not found")

    update_data["updated_at"] = datetime.now()
    template.sqlmodel_update(update_data)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


@router.delete("/")
async def delete_document_template(id: UUID, session: SessionDep):
    template = await session.get(DocumentTemplate, id)
    if not template:
        raise HTTPException(status_code=404, detail="Document Template not found")
    await session.delete(template)
    await session.commit()
    return {"detail": "Deleted"}


# ===================== Email Template Rendering =====================

class RenderEmailRequest(BaseModel):
    user_id: UUID


def _resolve(path: str, ctx: dict):
    """Resolve a dot-path like 'user.first_name' against a nested dict."""
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _render_email(content: str, ctx: dict) -> str:
    """
    Replace {{var.path}} placeholders and {{#list}}...{{/list}} loops.
    Same logic as project renderer, scoped to email context.
    """
    # 1. List loops: {{#documentation_links}}...{{/documentation_links}}
    loop_pat = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

    def loop_replacer(m):
        key = m.group(1)
        inner = m.group(2).strip()
        items = _resolve(key, ctx)
        if not isinstance(items, list):
            return ""
        out = []
        for item in items:
            if isinstance(item, dict):
                rendered = inner
                singular = key[:-1] if key.endswith("s") else key
                for k, v in item.items():
                    val = str(v) if v is not None else ""
                    rendered = rendered.replace(f"{{{{{singular}.{k}}}}}", val)
                    rendered = rendered.replace(f"{{{{{k}}}}}", val)
                out.append(rendered)
        return "\n".join(out)

    content = re.sub(loop_pat, loop_replacer, content, flags=re.DOTALL)

    # 2. Simple variables: {{user.first_name}}
    def replacer(m):
        path = m.group(1).strip()
        val = _resolve(path, ctx)
        if val is None:
            return m.group(0)   # leave unreplaced
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return str(val)

    return re.sub(r'\{\{([\w.]+)\}\}', replacer, content)


@router.post("/{template_id}/render-email")
async def render_email_template(
    template_id: UUID,
    body: RenderEmailRequest,
    session: SessionDep,
):
    """
    Render an email-type template for a specific user.
    Injects user info, org info, and all active integrations for that org.
    Returns the rendered text/HTML string.
    """
    template = await session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.type.value != "email":
        raise HTTPException(status_code=400, detail="Template is not of type 'email'")

    user = await session.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    org = user.organization

    # ── Teams ──────────────────────────────────────────────────────────────────
    teams_ctx: dict = {}
    if org:
        tg_res = await session.execute(
            select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org.id)
        )
        tg = tg_res.scalars().first()
        if tg:
            teams_ctx = {"name": tg.name, "external_id": tg.external_id}

    # ── Slack ──────────────────────────────────────────────────────────────────
    slack_client_ctx: dict = {}
    slack_partner_ctx: dict = {}
    if org:
        sc_res = await session.execute(
            select(OrganizationSlackChannel).where(OrganizationSlackChannel.organization_id == org.id)
        )
        for ch in sc_res.scalars().all():
            entry = {"channel_id": ch.external_id, "channel_name": ch.channel_name}
            if ch.channel_type == "client":
                slack_client_ctx = entry
            elif ch.channel_type == "ext_partner":
                slack_partner_ctx = entry

    # ── Jira ───────────────────────────────────────────────────────────────────
    jira_ctx: dict = {}
    if org:
        jp_res = await session.execute(
            select(OrganizationJiraProject).where(OrganizationJiraProject.organization_id == org.id)
        )
        jp = jp_res.scalars().first()
        if jp:
            jira_ctx = {
                "project_key": jp.project_key,
                "project_name": jp.project_name,
                "board_url": jp.board_url,
            }

    # ── Metabase ───────────────────────────────────────────────────────────────
    metabase_ctx: dict = {}
    if org:
        mb_res = await session.execute(
            select(OrganizationMetabaseGroup).where(OrganizationMetabaseGroup.organization_id == org.id)
        )
        mb = mb_res.scalars().first()
        if mb:
            metabase_ctx = {"name": mb.name, "external_id": mb.external_id}

    # ── Documentation links ────────────────────────────────────────────────────
    dl_res = await session.execute(select(DocumentationLink))
    doc_links = [
        {"title": lnk.title, "url": lnk.url, "description": lnk.description or ""}
        for lnk in dl_res.scalars().all()
    ]

    # ── Build full context ─────────────────────────────────────────────────────
    context = {
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "type": user.type.value if hasattr(user.type, "value") else str(user.type),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        },
        "organization": {
            "name": org.name if org else "",
            "industry": (org.industry or "") if org else "",
            "country": (org.country or "") if org else "",
        },
        "teams": teams_ctx,
        "slack_client": slack_client_ctx,
        "slack_partner": slack_partner_ctx,
        "jira": jira_ctx,
        "metabase": metabase_ctx,
        "documentation_links": doc_links,
    }

    rendered = _render_email(template.markdown_content, context)
    return {"rendered": rendered, "context": context}
