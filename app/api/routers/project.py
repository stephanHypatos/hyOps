
import os
import re
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlmodel import select

from app.database.models import (
    Project, ProjectStakeholder, ProjectUsecase, 
    User, Usecase,DocumentTemplate
)
from app.database.session import SessionDep
from app.api.schemas.project import (
    ProjectCreate, ProjectRead, ProjectUpdate,
    StakeholderRead, StakeholderReadEnriched, StakeholderAssign,
    UsecaseAssign, UsecaseRead, GeneratedDocumentReadEnriched, GenerateFromTemplatesRequest
)

from app.config import basedir


router = APIRouter(prefix="/project", tags=["Project"])


# ===================== Project CRUD Endpoints =====================

@router.get("/projects", response_model=list[ProjectRead])
async def get_all_projects(session: SessionDep):
    result = await session.execute(select(Project))
    return result.scalars().all()


@router.get("/", response_model=ProjectRead)
async def get_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=dict)
async def create_project(data: ProjectCreate, session: SessionDep):
    new_project = Project(**data.model_dump())
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"id": new_project.id}


@router.patch("/", response_model=ProjectRead)
async def update_project(id: UUID, data: ProjectUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data["updated_at"] = datetime.now()
    project.sqlmodel_update(update_data)
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/")
async def delete_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"detail": "Deleted"}


# ===================== Stakeholder M2M Endpoints =====================

@router.get("/{project_id}/stakeholders", response_model=list[StakeholderReadEnriched])
async def get_project_stakeholders(project_id: UUID, session: SessionDep):
    """
    Get stakeholders with enriched user details (name, email).
    Single query JOIN eliminates N+1 lookups on the frontend.
    """
    result = await session.execute(
        select(ProjectStakeholder, User)
        .join(User, ProjectStakeholder.user_id == User.id)
        .where(ProjectStakeholder.project_id == project_id)
    )
    rows = result.all()
    
    return [
        StakeholderReadEnriched(
            project_id=ps.project_id,
            user_id=ps.user_id,
            role=ps.role,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email
        )
        for ps, user in rows
    ]


@router.post("/{project_id}/stakeholder", response_model=StakeholderRead)
async def assign_stakeholder(project_id: UUID, data: StakeholderAssign, session: SessionDep):
    # Validate user exists
    user = await session.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate project exists
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check for duplicate
    existing = await session.get(ProjectStakeholder, (project_id, data.user_id))
    if existing:
        raise HTTPException(status_code=400, detail="User is already a stakeholder in this project")
    
    link = ProjectStakeholder(project_id=project_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{project_id}/stakeholder/{user_id}")
async def remove_stakeholder(project_id: UUID, user_id: UUID, session: SessionDep):
    link = await session.get(ProjectStakeholder, (project_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="Stakeholder not found in this project")
    await session.delete(link)
    await session.commit()
    return {"detail": "Stakeholder removed"}


# ===================== Usecase M2M Endpoints =====================

@router.get("/{project_id}/usecases", response_model=list[UsecaseRead])
async def get_project_usecases(project_id: UUID, session: SessionDep):
    result = await session.execute(
        select(ProjectUsecase).where(ProjectUsecase.project_id == project_id)
    )
    return result.scalars().all()


@router.post("/{project_id}/usecase")
async def assign_usecase(project_id: UUID, data: UsecaseAssign, session: SessionDep):
    # Validate usecase exists
    usecase = await session.get(Usecase, data.usecase_id)
    if not usecase:
        raise HTTPException(status_code=404, detail="Usecase not found")
    
    # Check for duplicate
    existing = await session.get(ProjectUsecase, (project_id, data.usecase_id))
    if existing:
        raise HTTPException(status_code=400, detail="Usecase is already in this project")
    
    link = ProjectUsecase(project_id=project_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{project_id}/usecase/{usecase_id}")
async def remove_usecase(project_id: UUID, usecase_id: UUID, session: SessionDep):
    link = await session.get(ProjectUsecase, (project_id, usecase_id))
    if not link:
        raise HTTPException(status_code=404, detail="Usecase not found in this project")
    await session.delete(link)
    await session.commit()
    return {"detail": "Usecase removed from project"}





# ===================== Document Generation Endpoint =====================




# ===================== Helper Functions =====================

PROJECT_SKIP = {
    "id", "created_at", "updated_at",
    "customer", "deal_winner", "stakeholders",
    "linked_usecases", "primary_usecase",
    "generated_documents", "erp_connectors", "hystudio_companies"
}
ORG_SKIP = {
    "id", "created_at", "updated_at",
    "users", "projects", "teams_groups", "slack_channels",
    "metabase_groups", "hystudio_companies", "erp_systems"
}
USER_SKIP = {
    "id", "created_at", "updated_at",
    "organization", "subtype", "languages", "skills",
    "won_projects", "owned_features", "created_templates",
    "projects", "teams_groups", "slack_channels",
    "metabase_groups", "hystudio_companies"
}
USECASE_SKIP = {"id", "features", "projects"}


def _serialize_value(val):
    if val is None:
        return ""
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    if isinstance(val, bool):
        return str(val).lower()
    if isinstance(val, (str, int, float)):
        return val
    if isinstance(val, list):
        return [_serialize_value(v) for v in val]
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    return str(val)



def _extract_fields(obj, skip_set):
    result = {}
    # Works with both Pydantic v1 and v2
    fields = getattr(type(obj), 'model_fields', None) or getattr(type(obj), '__sqlmodel_fields__', {})
    for col in fields:
        if col in skip_set:
            continue
        result[col] = _serialize_value(getattr(obj, col, None))
    return result


def build_render_context(project: Project) -> dict:
    """Build nested dict from Project ORM for {{project.name}} style placeholders."""
    context = {
        "project": _extract_fields(project, PROJECT_SKIP),
        "customer": _extract_fields(project.customer, ORG_SKIP) if project.customer else {},
        "deal_winner": _extract_fields(project.deal_winner, USER_SKIP) if project.deal_winner else {},
        "primary_usecase": _extract_fields(project.primary_usecase, USECASE_SKIP) if project.primary_usecase else {},
        "stakeholders": [],
    }

    if project.stakeholders:
        for user in project.stakeholders:
            context["stakeholders"].append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": getattr(user, 'email', ''),
                "phone": getattr(user, 'phone', ''),
                "type": str(getattr(user, 'type', '')),
                "subtype": str(getattr(user.subtype, 'name', '')) if hasattr(user, 'subtype') and user.subtype else '',
            })

    return context


def replace_placeholders(markdown_content: str, context: dict) -> str:
    """Pure regex replacement for {{project.name}}, {{customer.email}}, etc."""
    def replacer(match):
        var_path = match.group(1).strip()
        value = _resolve_dot_path(var_path, context)
        if value is None:
            # Fallback: bare key like {{name}} → try under "project"
            if "." not in var_path:
                value = _resolve_dot_path(f"project.{var_path}", context)
        if value is None:
            return match.group(0)
        if isinstance(value, list):
            if len(value) > 0 and isinstance(value[0], dict):
                lines = []
                for item in value:
                    lines.append("- " + ", ".join(f"{k}: {v}" for k, v in item.items()))
                return "\n".join(lines)
            return ", ".join(str(v) for v in value)
        if isinstance(value, dict):
            return ", ".join(f"{k}: {v}" for k, v in value.items())
        return str(value)

    pattern = r'\{\{([\w.]+)\}\}'
    return re.sub(pattern, replacer, markdown_content)


def _resolve_dot_path(path: str, context: dict):
    current = context
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def save_generated_file(output_dir: str, filename: str, content: str, file_format: str) -> str:
    """Save rendered content to disk as .md or .docx"""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    if file_format == "docx":
        from docx import Document
        doc = Document()
        for line in content.split('\n'):
            doc.add_paragraph(line)
        doc.save(file_path)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return file_path




def save_generated_file(output_dir: str, filename: str, content: str, file_format: str) -> str:
    """Save rendered content to disk as .md or .docx"""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    if file_format == "docx":
        from docx import Document
        doc = Document()
        for line in content.split('\n'):
            doc.add_paragraph(line)
        doc.save(file_path)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return file_path


# ===================== Template-Based Generation Endpoints =====================

@router.get("/{project_id}/generated-documents")
async def get_generated_documents(project_id: UUID, session: SessionDep):
    """
    List generated documents by scanning the file system.
    No database queries — just checks which files exist on disk.
    """
    output_dir = os.path.join(basedir, 'generated_documents', str(project_id))
    results = []

    # Get all active templates to check which ones have files
    result = await session.execute(select(DocumentTemplate))
    templates = result.scalars().all()

    for tmpl in templates:
        file_format = tmpl.file_format or 'md'
        filename = f"{tmpl.id}.{file_format}"
        file_path = os.path.join(output_dir, filename)

        if os.path.exists(file_path):
            results.append({
                "template_id": str(tmpl.id),
                "template_name": tmpl.name,
                "template_type": tmpl.type.value if hasattr(tmpl.type, 'value') else str(tmpl.type),
                "template_version": tmpl.version,
                "file_format": file_format,
                "status": "final",
                "created_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            })

    return results


@router.post("/{project_id}/generate-from-templates")
async def generate_from_templates(
    project_id: UUID,
    data: GenerateFromTemplatesRequest,
    session: SessionDep
):
    """
    Generate documents from selected templates.
    Saves files to disk only — NO database records created.
    Overwrites existing files for the same template.
    """
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    context = build_render_context(project)
    results = []

    for template_id in data.template_ids:
        template = await session.get(DocumentTemplate, template_id)
        if not template:
            continue

        # 1. Replace placeholders
        rendered = replace_placeholders(template.markdown_content, context)

        # 2. Save to disk with predictable filename: {template_id}.{format}
        file_format = template.file_format or 'md'
        output_dir = os.path.join(basedir, 'generated_documents', str(project_id))
        filename = f"{template_id}.{file_format}"
        file_path = save_generated_file(output_dir, filename, rendered, file_format)

        results.append({
            "template_id": str(template_id),
            "template_name": template.name,
            "template_type": template.type.value if hasattr(template.type, 'value') else str(template.type),
            "template_version": template.version,
            "file_format": file_format,
            "status": "final",
            "created_at": datetime.now().isoformat(),
        })

    return {
        "detail": f"Generated {len(results)} document(s) successfully",
        "documents": results
    }


@router.get("/{project_id}/download-template/{template_id}")
async def download_template_document(
    project_id: UUID,
    template_id: UUID,
    session: SessionDep
):
    """
    Download a generated document by project_id and template_id.
    Reads directly from disk — no database lookup needed.
    """
    template = await session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    file_format = template.file_format or 'md'
    filename = f"{template_id}.{file_format}"
    file_path = os.path.join(basedir, 'generated_documents', str(project_id), filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. Generate it first.")

    # Create a human-readable download filename
    safe_name = re.sub(r'[^\w]', '_', template.name)[:40]
    download_name = f"{safe_name}.{file_format}"

    if file_format == "docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_format == "md":
        media_type = "text/markdown"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_name
    )